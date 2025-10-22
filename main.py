
"""
Sistema de Agente IA Multimodal - 100% LOCAL
Sin Azure, sin OpenAI API, sin costos recurrentes
Ejecutable en laptop con GPU o CPU
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, Conversation, Message, create_db_and_tables
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

from settings import settings
from typing import Optional, List, Dict, Any
import base64
import json
import magic
from datetime import datetime
import hashlib
import subprocess
import tempfile
import os
from pathlib import Path
import asyncio
from collections import defaultdict
import time

create_db_and_tables()

app = FastAPI(
    title="Local AI Agent",
    description="Sistema IA 100% local sin costos cloud",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios


# ===== CACHÉ LOCAL (Sin Redis) =====
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LocalCache:
    """Caché en memoria + archivo para persistencia"""
    def __init__(self, cache_dir: Path, cache_ttl: int):
        self.cache_dir = cache_dir
        self.memory_cache: Dict[str, Any] = {}
        self.stats = {"hits": 0, "misses": 0}
        self._load_cache()

    def _get_key(self, content: Any) -> str:
        serialized = json.dumps(content, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def _load_cache(self):
        """Carga caché del disco al iniciar"""
        cache_file = self.cache_dir / "cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.memory_cache = json.load(f)
                print(f"✅ Caché cargado: {len(self.memory_cache)} entradas")
            except:
                pass

    def _save_cache(self):
        """Guarda caché en disco"""
        cache_file = self.cache_dir / "cache.json"
        with open(cache_file, 'w') as f:
            json.dump(self.memory_cache, f)

    def get(self, content: Any) -> Optional[dict]:
        key = self._get_key(content)
        if key in self.memory_cache:
            # Verificar expiración (1 hora)
            entry = self.memory_cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                self.stats["hits"] += 1
                return entry["data"]
            else:
                del self.memory_cache[key]
        self.stats["misses"] += 1
        return None

    def set(self, content: Any, data: dict):
        key = self._get_key(content)
        self.memory_cache[key] = {
            "data": data,
            "timestamp": time.time()
        }
        # Guardar cada 10 entradas
        if len(self.memory_cache) % 10 == 0:
            self._save_cache()

    def get_stats(self) -> dict:
        total = self.stats["hits"] + self.stats["misses"]
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": self.stats["hits"] / total if total > 0 else 0,
            "entries": len(self.memory_cache)
        }

cache = LocalCache(settings.CACHE_DIR, settings.CACHE_TTL)

# ===== RATE LIMITER LOCAL =====
class SimpleRateLimiter:
    """Rate limiter en memoria"""
    def __init__(self, max_requests: int, window: int):
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def check_limit(self, user_id: str) -> bool:
        now = time.time()
        cutoff = now - self.window
        # Limpiar requests antiguos
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]
        # Verificar límite
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        self.requests[user_id].append(now)
        return True

rate_limiter = SimpleRateLimiter(max_requests=settings.RATE_LIMIT_MAX_REQUESTS, window=settings.RATE_LIMIT_WINDOW)

# ===== MODELO LOCAL (Ollama) =====
class LocalModelManager:
    """Gestiona modelos locales vía Ollama"""
    def __init__(self, ollama_host: str, default_model: str, vision_model: str):
        self.ollama_url = ollama_host
        self.default_model = default_model
        self.vision_model = vision_model # Para imágenes
        self._check_ollama()

    def _check_ollama(self):
        """Verifica que Ollama esté corriendo"""
        try:
            import httpx
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=2.0)
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"✅ Ollama conectado. Modelos disponibles: {len(models)}")
            else:
                print("⚠ Ollama no responde. Instala con: curl -fsSL\nhttps://ollama.com/install.sh | sh")
        except Exception as e:
            print(f"❌ Error conectando a Ollama: {e}")
            print("Instala Ollama: https://ollama.com/download")

    async def complete(self, messages: List[dict], image_data: Optional[str] = None, stream: bool = False) -> Any:
        """Completa con modelo local"""
        import httpx
        # Si hay imagen, usar modelo de visión
        model = self.vision_model if image_data else self.default_model

        # Construir prompt
        prompt = self._build_prompt(messages)

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": stream
                }
                # Agregar imagen si existe
                if image_data:
                    payload["images"] = [image_data]

                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=120.0 # Modelos locales pueden ser lentos
                )

                if response.status_code == 200:
                    if stream:
                        async def stream_generator():
                            async for chunk in response.aiter_bytes():
                                try:
                                    # Ollama envía chunks de JSON, cada uno con una 'response' field
                                    # Necesitamos decodificar cada línea si son múltiples JSONs por chunk
                                    for line in chunk.decode().split('\n'):
                                        if line.strip():
                                            json_data = json.loads(line)
                                            if "response" in json_data:
                                                yield json_data["response"]
                                except json.JSONDecodeError:
                                    # Esto puede ocurrir si un chunk no es un JSON completo
                                    # Podríamos loggear o simplemente ignorar chunks incompletos
                                    pass
                        return stream_generator()
                    else:
                        result = response.json()
                        return {
                            "content": result["response"],
                            "model": model,
                            "tokens": result.get("eval_count", 0),
                            "cost": 0.0 # ¡Gratis!
                        }
                else:
                    raise Exception(f"Ollama error: {response.text}")
        except Exception as e:
            return {
                "content": f"Error en modelo local: {str(e)}",
                "model": "error",
                "cost": 0.0,
                "error": str(e)
            }

    def _build_prompt(self, messages: List[dict]) -> str:
        """Construye prompt desde mensajes"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, list):
                # Contenido multimodal
                text_parts = [
                    item.get("text", "")
                    for item in content
                    if item.get("type") == "text"
                ]
                content = " ".join(text_parts)

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        return "\n\n".join(prompt_parts) + "\n\nAssistant:"

model_manager = LocalModelManager(settings.OLLAMA_HOST, settings.DEFAULT_MODEL, settings.VISION_MODEL)

# ===== WHISPER LOCAL =====
class LocalWhisper:
    """Transcripción de audio con Whisper local"""
    def __init__(self, use_whisper: bool, whisper_model: str):
        self.model_loaded = False
        self.use_whisper = use_whisper
        self.whisper_model = whisper_model
        if self.use_whisper:
            self._check_whisper()

    def _check_whisper(self):
        """Verifica instalación de Whisper"""
        try:
            import whisper
            self.model = whisper.load_model(self.whisper_model) # base, small, medium, large
            self.model_loaded = True
            print("✅ Whisper cargado (modelo: base)")
        except ImportError:
            print("⚠ Whisper no instalado. Instala con: pip install openai-whisper")
        except Exception as e:
            print(f"❌ Error cargando Whisper: {e}")

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio"""
        if not self.use_whisper or not self.model_loaded:
            return "[Whisper no disponible - instala con: pip install openai-whisper]"

        import whisper
        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
        try:
            result = self.model.transcribe(tmp.name)
            return result["text"]
        except Exception as e:
            return f"[Error transcribiendo: {e}]"
        finally:
            os.unlink(tmp.name)

whisper_local = LocalWhisper(settings.USE_WHISPER, settings.WHISPER_MODEL)

# ===== EJECUTOR SEGURO =====
class LocalExecutor:
    """Ejecuta código de forma segura localmente"""
    def __init__(self, timeout: int, max_output: int):
        self.timeout = timeout
        self.max_output = max_output # Caracteres

    async def execute_python(self, code: str) -> dict:
        # Validación básica para evitar comandos del sistema en Python
        if any(keyword in code for keyword in ['os.system', 'subprocess.run', 'subprocess.Popen', '__import__("os")']):
            return {"success": False, "error": "Comandos del sistema no permitidos en el código Python."}

        """Ejecuta Python en subprocess"""
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.flush()
            # Ejecutar con timeout
            result = subprocess.run(
                ["python", f.name],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:self.max_output],
                "stderr": result.stderr[:self.max_output]
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout ({self.timeout}s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            # Eliminar archivo temporal
            if 'f' in locals() and f.name:
                try:
                    os.unlink(f.name)
                except:
                    pass

    async def execute_bash(self, command: str) -> dict:
        # Validación básica para evitar comandos peligrosos en Bash
        if any(keyword in command for keyword in ['rm -rf', 'sudo', 'mkfs', 'dd', 'chmod 777', 'chown']):
            return {"success": False, "error": "Comandos peligrosos no permitidos en Bash."}

        """Ejecuta comando bash"""
        try:
            result = subprocess.run(
                ['bash', '-c', command], # Ejecutar explícitamente con bash para mejor control
                capture_output=True,
                text=True,
                timeout=self.timeout,
                # Añadir preexec_fn para restringir permisos (limitado en sandbox)
                # preexec_fn=lambda: os.setuid(1000) # Ejecutar como un usuario sin privilegios (ej. usuario 'sandbox' en Docker)
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:self.max_output],
                "stderr": result.stderr[:self.max_output]
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout ({self.timeout}s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

executor = LocalExecutor(settings.EXECUTOR_TIMEOUT, settings.EXECUTOR_MAX_OUTPUT)

# ===== LOGGING =====
def log_request(endpoint: str, user_id: str, duration: float, status: str):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "user_id": user_id,
        "duration_ms": round(duration * 1000, 2),
        "status": status
    }
    log_file = settings.LOGS_DIR / f"requests_{datetime.now().strftime("%Y%m%d")}.log"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")

# ===== ENDPOINT PRINCIPAL =====
@app.post("/process")
async def process_local(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user_id: str = Form("anonymous"),
    stream: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    Endpoint principal que procesa cualquier entrada
    100% local, sin costos de API
    """
    start_time = time.time()

    # Rate Limiter
    if not rate_limiter.check_limit(user_id):
        raise HTTPException(status_code=429, detail="Límite de peticiones excedido")

    try:
        # Recuperar historial de conversación
        conversation = db.query(Conversation).filter(Conversation.user_id == user_id).first()
        if not conversation:
            conversation = Conversation(user_id=user_id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        messages = []
        for msg in conversation.messages:
            messages.append({"role": msg.role, "content": msg.content})

        # Añadir el nuevo mensaje del usuario al historial
        if text:
            messages.append({"role": "user", "content": text})
            user_message_db = Message(conversation_id=conversation.id, role="user", content=text)
            db.add(user_message_db)
            db.commit()
            db.refresh(user_message_db)

        # Procesar archivo si existe
        image_data = None
        metadata = {}
        if file:
            if file.size > settings.MAX_UPLOAD_SIZE * 1024 * 1024:
                raise HTTPException(413, f"Archivo demasiado grande > {settings.MAX_UPLOAD_SIZE}MB")
            file_bytes = await file.read()
            # Usar python-magic para una detección más precisa
            try:
                mime_type = magic.from_buffer(file_bytes, mime=True)
            except Exception:
                mime_type = file.content_type # Fallback a content_type de FastAPI
            metadata["filename"] = file.filename
            metadata["size"] = len(file_bytes)
            metadata["mime_type"] = mime_type

            # Si es imagen, convertir a base64
            if mime_type.startswith("image/"):
                image_data = base64.b64encode(file_bytes).decode("utf-8")
            elif mime_type.startswith("audio/"):
                if settings.USE_WHISPER:
                    transcript = await whisper_local.transcribe(file_bytes)
                else:
                    transcript = "[Transcripción de audio deshabilitada]"
                messages.append({"role": "user", "content": f"[Audio: {file.filename}]\n{transcript}"})
            else:
                # Para otros archivos, usar el texto si se proporciona
                if not text:
                    messages.append({"role": "user", "content": f"[Archivo: {file.filename}]"})

        # Llamar al modelo local
        model_response = await model_manager.complete(messages, image_data, stream=stream)

        if stream:
            async def stream_and_save_generator():
                full_response_content = ""
                async for chunk in model_response:
                    full_response_content += chunk
                    yield chunk
                # Guardar la respuesta completa del asistente después del stream
                assistant_message_db = Message(conversation_id=conversation.id, role="assistant", content=full_response_content)
                db.add(assistant_message_db)
                db.commit()
                db.refresh(assistant_message_db)

            return StreamingResponse(stream_and_save_generator(), media_type="text/event-stream")
        else:
            # No streaming: procesar la respuesta completa
            result_content = model_response["content"]
            model_name = model_response["model"]
            tokens_used = model_response["tokens"]
            cost = model_response["cost"]

            # Verificar si necesita ejecutar código
            if "```python" in result_content:
                code = result_content.split("```python")[1].split("```")[0].strip()
                exec_result = await executor.execute_python(code)
                result_content += f"\n\n[Resultado de ejecución]\n{exec_result['stdout']}"

            # Guardar la respuesta del asistente
            assistant_message_db = Message(conversation_id=conversation.id, role="assistant", content=result_content)
            db.add(assistant_message_db)
            db.commit()
            db.refresh(assistant_message_db)

            result = {
                "response": result_content,
                "model": model_name,
                "cost": cost,
                "metadata": metadata,
                "processing_time": round(time.time() - start_time, 2),
                "from_cache": False
            }
            return JSONResponse(result)

    except HTTPException:
        raise
    except Exception as e:
        log_request("/process", user_id, time.time() - start_time, "error")
        raise HTTPException(status_code=500, detail=str(e))

# ===== OTROS ENDPOINTS =====
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/cache/stats")
def cache_stats():
    return cache.get_stats()

@app.on_event("shutdown")
def on_shutdown():
    print("💾 Guardando caché antes de salir...")
    cache._save_cache()

if __name__ == "__main__":
    import uvicorn
    print("🚀 Servidor FastAPI listo en http://localhost:8000")
    print(f"📁 Directorio base: {settings.BASE_DIR}")
    print(f"💾 Caché: {settings.CACHE_DIR}")
    print(f"📝 Logs: {settings.LOGS_DIR}")
    print(f"📤 Uploads: {settings.UPLOADS_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8000)

