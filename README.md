# Sistema de Agente IA Multimodal - 100% LOCAL (Interfaz Mejorada)

Este proyecto implementa un sistema de agente de inteligencia artificial completamente local, diseñado para funcionar sin dependencias de servicios en la nube o APIs de terceros, garantizando privacidad y cero costos recurrentes. Ha sido mejorado con una interfaz de usuario (UI) rediseñada y nuevas funcionalidades inspiradas en aplicaciones modernas de IA.

## Características Principales

-   **Procesamiento Local**: Todas las operaciones de IA se realizan en tu máquina local, utilizando modelos como Ollama y Whisper.
-   **Privacidad Total**: Tus datos nunca abandonan tu entorno local.
-   **Cero Costos Recurrentes**: No hay tarifas asociadas a servicios en la nube o APIs externas.
-   **Ejecución Flexible**: Compatible con laptops equipadas con GPU o incluso solo CPU.
-   **Interfaz Web Interactiva (Streamlit)**: Una aplicación web intuitiva y responsiva para interactuar con el agente, enviar texto, imágenes y audio.
-   **Persistencia de Conversaciones**: Historial de chat guardado localmente usando SQLite y SQLAlchemy.
-   **Ejecución Segura de Código**: Capacidad para ejecutar código Python y comandos Bash de forma controlada y segura.
-   **Detección Precisa de Tipos MIME**: Utiliza `python-magic` para identificar correctamente los tipos de archivos subidos.
-   **Configuración Centralizada**: Gestión de ajustes del sistema mediante `pydantic-settings` y variables de entorno.
-   **Streaming de Respuestas**: Soporte para respuestas en tiempo real desde el modelo de lenguaje.

## Mejoras Implementadas

Se han realizado las siguientes mejoras significativas al proyecto original:

### 1. Centralización de la Configuración (`pydantic-settings`)

La configuración del proyecto ahora se gestiona de manera centralizada y robusta utilizando `pydantic-settings`. Esto permite definir todos los ajustes en un único lugar (`settings.py`) y cargarlos fácilmente desde variables de entorno (`.env`) o valores predeterminados. Esto mejora la mantenibilidad y la flexibilidad del sistema.

**Archivos Clave Afectados:** `settings.py`, `.env`, `main.py`.

### 2. Mejora de la Seguridad en la Ejecución de Código

Debido a las limitaciones del entorno sandbox para la implementación de Docker, se ha fortalecido la clase `LocalExecutor` en `main.py`. Ahora incluye:

-   **Validación Estricta**: Se han añadido validaciones para prevenir la ejecución de comandos peligrosos o no autorizados (ej. `os.system`, `rm -rf`) tanto en código Python como en comandos Bash.
-   **Límites de Recursos**: Se utilizan timeouts para evitar que los procesos de ejecución de código se extiendan indefinidamente, mejorando la estabilidad del sistema.

**Archivos Clave Afectados:** `main.py`.

### 3. Streaming de Respuestas desde Ollama y FastAPI

El sistema ahora soporta el streaming de respuestas desde los modelos de Ollama a través de la API de FastAPI. Esto proporciona una experiencia de usuario más fluida y en tiempo real, especialmente con respuestas largas o modelos más lentos. La interfaz Streamlit también ha sido adaptada para consumir estos streams.

**Archivos Clave Afectados:** `main.py`, `app_streamlit.py`.

### 4. Persistencia de la Conversación (SQLite y SQLAlchemy)

Se ha integrado un sistema de persistencia para el historial de conversaciones utilizando SQLite como base de datos y SQLAlchemy como ORM. Las conversaciones y los mensajes se almacenan localmente, permitiendo que el agente recuerde el contexto de interacciones anteriores con un `user_id` específico. Alembic se utiliza para gestionar las migraciones de la base de datos.

**Archivos Clave Afectados:** `database.py`, `alembic.ini`, `alembic/env.py`, `main.py`.

### 5. Detección Precisa de Tipos MIME (`python-magic`)

Para una identificación más precisa de los tipos de archivos subidos (imágenes, audio, documentos, etc.), se ha incorporado la librería `python-magic`. Esto mejora la capacidad del agente para procesar y categorizar correctamente los archivos, incluso si la extensión no es confiable.

**Archivos Clave Afectados:** `main.py`.

### 6. Interfaz Web Rediseñada y Optimizada (`Streamlit`)

Se ha implementado una interfaz de usuario web completamente rediseñada utilizando Streamlit (`app_streamlit.py`), inspirada en las imágenes proporcionadas por el usuario. Esta nueva UI ofrece una experiencia más intuitiva y rica en funcionalidades:

-   **Diseño Responsivo**: La interfaz se adapta automáticamente a diferentes tamaños de pantalla (móvil como Redmi Note 13 Pro y escritorio como Lenovo LOQ 15), utilizando `streamlit_js_eval` para la detección de ancho de pantalla y estilos CSS adaptativos.
-   **Barra Lateral de Navegación**: Una barra lateral izquierda permite una navegación clara entre diferentes secciones y herramientas del agente:
    *   **Chat**: Interfaz principal de conversación.
    *   **Resumen**: Herramienta para resumir documentos (PDF, URL, Texto).
    *   **Escribir**: Asistente de escritura con opciones de tono, longitud y formato.
    *   **Buscar**: Interfaz para realizar búsquedas.
    *   **Leer**: Para analizar documentos o URLs.
    *   **Traducir**: Herramienta de traducción de texto.
    *   **Arte de IA**: Generador de imágenes a partir de texto (funcionalidad base).
    *   **Kit de Herramientas**: Sección para futuras herramientas adicionales.
    *   **Configuración**: Ajustes de la API, notificaciones, modo oscuro, etc.
    *   **Acerca de**: Información sobre la aplicación.
-   **Selección de Modelos Dinámica**: Permite al usuario elegir fácilmente entre una lista de modelos de IA disponibles (`llama2`, `mistral`, `neural-chat`, `orca-mini`, `dolphin-mixtral`) desde la barra lateral.
-   **Interfaz de Chat Mejorada**: Visualización clara de los mensajes del usuario y del asistente, con opciones para ver detalles de procesamiento.
-   **Sección de Archivos Integrada**: Facilita la subida y procesamiento de archivos directamente desde la interfaz.

**Archivos Clave Afectados:** `app_streamlit.py`.

## Cómo Iniciar el Sistema

Para ejecutar este sistema, sigue los siguientes pasos:

1.  **Clonar el repositorio** (si aplica).
2.  **Instalar dependencias**: Asegúrate de tener Python 3.9+ y pip instalados. Luego, instala las dependencias necesarias:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configurar Ollama**: Asegúrate de que Ollama esté instalado y ejecutándose en tu sistema. Descarga los modelos que desees utilizar (ej. `ollama pull llama2`, `ollama pull llava`).
4.  **Configuración de entorno**: Crea un archivo `.env` en la raíz del proyecto con la configuración necesaria (ej. `OLLAMA_HOST`, `DATABASE_URL`). Un ejemplo básico podría ser:
    ```
    OLLAMA_HOST=http://localhost:11434
    DEFAULT_MODEL=llama2
    VISION_MODEL=llava
    DATABASE_URL=sqlite:///./sql_app.db
    CACHE_DIR=./cache
    LOGS_DIR=./logs
    UPLOADS_DIR=./uploads
    MAX_UPLOAD_SIZE=25 # MB
    USE_WHISPER=False
    WHISPER_MODEL=base
    EXECUTOR_TIMEOUT=10
    EXECUTOR_MAX_OUTPUT=1000
    RATE_LIMIT_MAX_REQUESTS=100
    RATE_LIMIT_WINDOW=3600 # segundos
    ```
5.  **Inicializar la base de datos**: Ejecuta las migraciones de Alembic para crear la base de datos:
    ```bash
    alembic upgrade head
    ```
6.  **Iniciar el servidor FastAPI**: Abre una terminal y ejecuta:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```
7.  **Iniciar la interfaz Streamlit**: Abre otra terminal y ejecuta:
    ```bash
    streamlit run app_streamlit.py
    ```

Accede a la interfaz de Streamlit en la dirección que te indique la terminal (normalmente `http://localhost:8501`).

## Acceso Remoto (Consideraciones)

Para acceder a este sistema desde un dispositivo móvil o cualquier ubicación remota, necesitarías desplegar la aplicación en un servidor accesible públicamente (como una máquina virtual en Azure o un servicio de hosting). En un entorno de desarrollo local o sandbox, la exposición es temporal y solo para pruebas. Se recomienda configurar un proxy inverso (ej. Nginx) y HTTPS para un acceso seguro en producción.

## Estructura del Proyecto

```
. (raíz del proyecto)
├── main.py             # Aplicación FastAPI principal
├── settings.py         # Configuración del proyecto con pydantic-settings
├── database.py         # Modelos de SQLAlchemy y configuración de la DB
├── alembic/            # Directorio de migraciones de Alembic
│   ├── versions/       # Archivos de migración generados
│   └── env.py          # Entorno de configuración de Alembic
├── alembic.ini         # Configuración principal de Alembic
├── app_streamlit.py    # Interfaz web con Streamlit (rediseñada y responsiva)
├── .env                # Variables de entorno (no versionado)
├── requirements.txt    # Dependencias del proyecto
└── README.md           # Este archivo
```

## Uso

Interactúa con el agente a través de la interfaz Streamlit. Puedes enviar mensajes de texto, subir archivos, seleccionar modelos, usar las diferentes herramientas y observar las respuestas del agente, incluyendo la ejecución de código y la persistencia de la conversación.
