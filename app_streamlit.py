import streamlit as st
import requests
import json
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

# Configuración de la página
st.set_page_config(
    page_title="Local AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados responsivos
st.markdown("""
    <style>
    /* Estilos generales */
    .main {
        padding: 1rem;
    }
    
    /* Sidebar personalizado */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f5f5f5 0%, #ffffff 100%);
    }
    
    /* Botones de herramientas */
    .tool-button {
        width: 100%;
        padding: 0.75rem;
        margin: 0.25rem 0;
        border-radius: 0.5rem;
        border: 2px solid #e0e0e0;
        background-color: #f9f9f9;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    
    .tool-button:hover {
        border-color: #6366f1;
        background-color: #e0e7ff;
    }
    
    .tool-button.active {
        border-color: #6366f1;
        background-color: #6366f1;
        color: white;
    }
    
    /* Selector de modelos */
    .model-selector {
        padding: 1rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-bottom: 1rem;
    }
    
    /* Tarjetas de contenido */
    .content-card {
        padding: 1.5rem;
        border-radius: 0.75rem;
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    
    /* Mensajes de chat */
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.75rem;
        display: flex;
        gap: 0.75rem;
    }
    
    .chat-message.user {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    
    .chat-message.assistant {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    /* Opciones de herramientas */
    .tool-options {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    .option-button {
        padding: 0.5rem 1rem;
        border-radius: 1.5rem;
        border: 1px solid #ddd;
        background-color: #f5f5f5;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s ease;
    }
    
    .option-button:hover {
        background-color: #e0e0e0;
    }
    
    .option-button.selected {
        background-color: #6366f1;
        color: white;
        border-color: #6366f1;
    }
    
    /* Optimización para móvil */
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        
        .tool-options {
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
        }
        
        .content-card {
            padding: 1rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Función para detectar el ancho de pantalla
def get_screen_width():
    try:
        width = streamlit_js_eval(javascript="window.innerWidth", key="screen_width")
        return width if width else 1920
    except:
        return 1920

# Detectar dispositivo
screen_width = get_screen_width()
is_mobile = screen_width < 768

# Inicializar estado de sesión
if "current_tool" not in st.session_state:
    st.session_state.current_tool = "chat"
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "llama2"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"

# Configuración de la API
st.session_state.api_url = st.sidebar.text_input("API URL", value=st.session_state.api_url, key="api_url_input")
st.session_state.user_id = st.sidebar.text_input("ID de Usuario", value="anonymous", key="user_id_input")

st.sidebar.divider()

# Selector de modelos
st.sidebar.markdown("### 🤖 Modelos Disponibles")
models = {
    "llama2": "🦙 Llama 2",
    "mistral": "🌟 Mistral",
    "neural-chat": "💬 Neural Chat",
    "orca-mini": "🐋 Orca Mini",
    "dolphin-mixtral": "🐬 Dolphin Mixtral"
}

st.session_state.selected_model = st.sidebar.selectbox(
    "Selecciona un modelo:",
    options=list(models.keys()),
    format_func=lambda x: models[x],
    key="model_selector"
)

st.sidebar.divider()

# Navegación de herramientas
st.sidebar.markdown("### 🛠️ Herramientas")

tools = {
    "chat": ("💬", "Chat"),
    "resumen": ("📄", "Resumen"),
    "escribir": ("✍️", "Escribir"),
    "buscar": ("🔍", "Buscar"),
    "leer": ("📖", "Leer"),
    "traducir": ("🌐", "Traducir"),
    "arte": ("🎨", "Arte de IA"),
    "herramientas": ("🧰", "Kit de Herramientas"),
}

for tool_key, (icon, label) in tools.items():
    if st.sidebar.button(f"{icon} {label}", key=f"tool_{tool_key}", use_container_width=True):
        st.session_state.current_tool = tool_key

st.sidebar.divider()

# Opciones adicionales
if st.sidebar.button("⚙️ Configuración", use_container_width=True):
    st.session_state.current_tool = "settings"

if st.sidebar.button("ℹ️ Acerca de", use_container_width=True):
    st.session_state.current_tool = "about"

# Contenido principal
st.title("🤖 Local AI Agent")
st.markdown(f"**Modelo seleccionado:** {models[st.session_state.selected_model]}")

# Mostrar contenido según la herramienta seleccionada
if st.session_state.current_tool == "chat":
    st.header("💬 Chat")
    
    # Mostrar historial de mensajes
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input del usuario
    user_input = st.chat_input("Escribe tu pregunta...")
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.spinner("Procesando..."):
            try:
                data = {
                    "text": user_input,
                    "user_id": st.session_state.user_id,
                    "stream": False
                }
                
                response = requests.post(
                    f"{st.session_state.api_url}/process",
                    data=data,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_message = result.get("response", "Sin respuesta")
                    
                    st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                    
                    with st.chat_message("assistant"):
                        st.markdown(assistant_message)
                    
                    with st.expander("📋 Detalles"):
                        col1, col2, col3 = st.columns(3) if not is_mobile else [st.columns(1)[0], st.columns(1)[0], st.columns(1)[0]]
                        with col1:
                            st.metric("Modelo", result.get("model", "N/A"))
                        with col2:
                            st.metric("Tiempo (s)", result.get("processing_time", 0))
                        with col3:
                            st.metric("Costo", f"${result.get('cost', 0):.4f}")
                else:
                    st.error(f"Error: {response.status_code}")
            
            except requests.exceptions.ConnectionError:
                st.error(f"❌ No se puede conectar a la API en {st.session_state.api_url}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif st.session_state.current_tool == "resumen":
    st.header("📄 Generador de Resúmenes")
    
    st.markdown("Selecciona el tipo de contenido a resumir:")
    
    col1, col2, col3 = st.columns(3) if not is_mobile else [st.columns(1)[0], st.columns(1)[0], st.columns(1)[0]]
    
    with col1:
        if st.button("📄 PDF Document", use_container_width=True):
            st.session_state.summary_type = "pdf"
    
    with col2:
        if st.button("🌐 URL/Web Page", use_container_width=True):
            st.session_state.summary_type = "url"
    
    with col3:
        if st.button("📝 Texto", use_container_width=True):
            st.session_state.summary_type = "text"
    
    if "summary_type" in st.session_state:
        st.divider()
        
        if st.session_state.summary_type == "pdf":
            st.markdown("### Subir PDF")
            uploaded_file = st.file_uploader("Selecciona un archivo PDF", type="pdf")
            if uploaded_file:
                st.success(f"Archivo cargado: {uploaded_file.name}")
                if st.button("Resumir PDF"):
                    st.info("Resumiendo PDF...")
        
        elif st.session_state.summary_type == "url":
            st.markdown("### Ingresa una URL")
            url = st.text_input("Pega la URL de la página web:")
            if url:
                if st.button("Resumir URL"):
                    st.info(f"Resumiendo contenido de: {url}")
        
        elif st.session_state.summary_type == "text":
            st.markdown("### Ingresa el texto")
            text = st.text_area("Pega el texto a resumir:", height=200)
            if text:
                if st.button("Resumir Texto"):
                    st.info("Resumiendo texto...")

elif st.session_state.current_tool == "escribir":
    st.header("✍️ Herramienta de Escritura")
    
    st.markdown("### Opciones de Escritura")
    
    col1, col2 = st.columns(2) if not is_mobile else [st.columns(1)[0], st.columns(1)[0]]
    
    with col1:
        action = st.selectbox(
            "¿Qué deseas hacer?",
            ["Redactar", "Responder", "Verificar Gramática"]
        )
    
    with col2:
        tone = st.selectbox(
            "Tono:",
            ["Automático", "Amistoso", "Informal", "Profesional", "Formal"]
        )
    
    st.markdown("### Longitud")
    length = st.select_slider(
        "Selecciona la longitud:",
        options=["Corto", "Medio", "Largo"],
        value="Medio"
    )
    
    st.markdown("### Formato")
    format_type = st.selectbox(
        "Formato de salida:",
        ["Automático", "Correo electrónico", "Mensaje", "Comentario", "Párrafo", "Artículo", "Entrada de blog", "Ideas", "Esquema", "Twitter"]
    )
    
    st.markdown("### Contenido")
    content = st.text_area("Escribe o pega el contenido a editar:", height=200)
    
    if content and st.button("Procesar", use_container_width=True):
        st.info(f"Procesando con tono {tone} en formato {format_type}...")

elif st.session_state.current_tool == "buscar":
    st.header("🔍 Búsqueda")
    
    search_query = st.text_input("¿Qué deseas buscar?", placeholder="Ingresa tu búsqueda...")
    
    if search_query and st.button("Buscar", use_container_width=True):
        st.info(f"Buscando: {search_query}")
        st.markdown("**Resultados rápidos:**")
        st.markdown("- Resultado 1")
        st.markdown("- Resultado 2")
        st.markdown("- Resultado 3")

elif st.session_state.current_tool == "leer":
    st.header("📖 Leer y Analizar")
    
    st.markdown("Sube un documento o proporciona un enlace para que sea analizado.")
    
    col1, col2 = st.columns(2) if not is_mobile else [st.columns(1)[0], st.columns(1)[0]]
    
    with col1:
        uploaded_file = st.file_uploader("Sube un archivo", type=["pdf", "txt", "docx"])
        if uploaded_file:
            st.success(f"Archivo cargado: {uploaded_file.name}")
    
    with col2:
        url = st.text_input("O proporciona una URL:")
        if url:
            st.success(f"URL ingresada: {url}")

elif st.session_state.current_tool == "traducir":
    st.header("🌐 Traductor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source_lang = st.selectbox("Idioma de origen:", ["Español", "Inglés", "Francés", "Alemán", "Italiano"])
    
    with col2:
        target_lang = st.selectbox("Idioma de destino:", ["Inglés", "Español", "Francés", "Alemán", "Italiano"])
    
    text_to_translate = st.text_area("Texto a traducir:", height=200)
    
    if text_to_translate and st.button("Traducir", use_container_width=True):
        st.info(f"Traduciendo de {source_lang} a {target_lang}...")

elif st.session_state.current_tool == "arte":
    st.header("🎨 Generador de Arte con IA")
    
    st.markdown("Describe la imagen que deseas generar:")
    
    prompt = st.text_area("Descripción de la imagen:", placeholder="Ej: Un gato astronauta en Marte...", height=150)
    
    col1, col2 = st.columns(2) if not is_mobile else [st.columns(1)[0], st.columns(1)[0]]
    
    with col1:
        style = st.selectbox("Estilo:", ["Realista", "Artístico", "Cartoon", "Abstracto", "Cyberpunk"])
    
    with col2:
        quality = st.selectbox("Calidad:", ["Estándar", "Alta", "Ultra"])
    
    if prompt and st.button("Generar Imagen", use_container_width=True):
        st.info("Generando imagen...")
        st.warning("⚠️ La generación de imágenes requiere una suscripción premium")

elif st.session_state.current_tool == "herramientas":
    st.header("🧰 Kit de Herramientas")
    
    st.markdown("Herramientas adicionales disponibles:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Análisis de Datos")
        st.markdown("Analiza y visualiza tus datos")
    
    with col2:
        st.markdown("#### 🔧 Utilidades")
        st.markdown("Herramientas útiles para tareas comunes")

elif st.session_state.current_tool == "settings":
    st.header("⚙️ Configuración")
    
    st.markdown("### Preferencias Generales")
    
    enable_notifications = st.checkbox("Habilitar notificaciones", value=True)
    dark_mode = st.checkbox("Modo oscuro", value=False)
    auto_save = st.checkbox("Guardar automáticamente", value=True)
    
    st.markdown("### API")
    st.text(f"URL actual: {st.session_state.api_url}")
    st.text(f"Usuario: {st.session_state.user_id}")
    
    if st.button("Probar conexión", use_container_width=True):
        try:
            response = requests.get(f"{st.session_state.api_url}/health")
            if response.status_code == 200:
                st.success("✅ Conexión exitosa")
            else:
                st.error("❌ Error en la conexión")
        except:
            st.error("❌ No se puede conectar a la API")

elif st.session_state.current_tool == "about":
    st.header("ℹ️ Acerca de")
    
    st.markdown("""
    ### Local AI Agent
    
    Un sistema de inteligencia artificial 100% local, sin costos de API y completamente privado.
    
    **Características:**
    - Procesamiento local de IA
    - Múltiples herramientas integradas
    - Interfaz intuitiva y responsiva
    - Soporte para múltiples modelos
    
    **Versión:** 2.0.0
    **Última actualización:** 2025-01-21
    """)

# Footer
st.divider()
st.markdown(f"""
    <div style="text-align: center; color: gray; font-size: 0.8rem;">
        <p>Sistema de IA Local • Sin costos de API • 100% privado</p>
        <p>Última actualización: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
""", unsafe_allow_html=True)

