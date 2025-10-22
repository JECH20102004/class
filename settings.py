from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # Directorios
    BASE_DIR: Path = Path(__file__).parent
    CACHE_DIR: Path = BASE_DIR / "cache"
    LOGS_DIR: Path = BASE_DIR / "logs"
    UPLOADS_DIR: Path = BASE_DIR / "uploads"

    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    DEFAULT_MODEL: str = "llama3.1:8b"
    VISION_MODEL: str = "llava:13b"

    # Ejecutor de código
    EXECUTOR_TIMEOUT: int = 10
    EXECUTOR_MAX_OUTPUT: int = 5000

    # Caché
    CACHE_TTL: int = 3600 # segundos

    # Rate Limiter
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600 # segundos

    # Whisper
    USE_WHISPER: bool = True
    WHISPER_MODEL: str = "base"

    # Otros
    LOG_LEVEL: str = "INFO"
    MAX_UPLOAD_SIZE: int = 100 # MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # Ignorar variables de entorno no definidas en Settings

settings = Settings()

# Crear directorios si no existen
for dir_path in [settings.CACHE_DIR, settings.LOGS_DIR, settings.UPLOADS_DIR]:
    dir_path.mkdir(exist_ok=True)

