import streamlit as st
import pandas as pd
import database
import auth

# Configuración de la página (¡llamarla primero!)
st.set_page_config(page_title="Gestor de Centros", layout="wide", initial_sidebar_state="collapsed")

# --- FUNCIÓN DE LOGIN ---
def login_screen():
    """
    Muestra la pantalla de inicio de sesión y gestiona el login.
    """
    st.title("Gestor de Centros Educativos 🇨🇷")
    st.header("Inicio de Sesión")

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

    if submitted:
        user_data = database.get_user(username)
        if user_data:
            if user_data.get("is_locked"):
                st.error("Este usuario ha sido bloqueado por demasiados intentos fallidos. Solicite al administrador el cambio y desbloqueo de contraseña.")
                return
            if auth.check_password(password, user_data["password_hash"]):
                # Login exitoso
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user_data["id"]
                st.session_state["username"] = user_data["username"]
                st.session_state["role"] = user_data["role"]
                st.session_state["full_name"] = user_data["full_name"]
                database.reset_failed_attempts(username)
                st.rerun()
            else:
                database.increment_failed_attempts(username)
                user_data = database.get_user(username)  # refrescar datos
                if user_data.get("is_locked"):
                    st.error("Usuario bloqueado tras 5 intentos fallidos. Solicite al administrador el cambio y desbloqueo de contraseña.")
                else:
                    st.error("Usuario o contraseña incorrectos")
        else:
            st.toast("Usuario o contraseña incorrectos", icon="❌")

# --- APLICACIÓN PRINCIPAL (POST-LOGIN) ---
def main_app():
    # --- Cierre de sesión por inactividad ---
    import time
    INACTIVITY_TIMEOUT = 900  # 15 minutos en segundos
    now = int(time.time())
    last_active = st.session_state.get("last_active", now)
    if now - last_active > INACTIVITY_TIMEOUT:
        st.session_state.clear()
        st.warning("Sesión cerrada por inactividad. Por favor, inicie sesión nuevamente.")
        st.stop()
    st.session_state["last_active"] = now

    # Intentar importar las vistas de forma perezosa (evita fallos en import)
    def mostrar_error_importacion(vista, error):
        st.error(f"La vista de {vista} no está disponible debido a un error de importación: {error}. Revisa las dependencias.")

    try:
        import admin_view
    except Exception as e:
        admin_view = None
        mostrar_error_importacion("administrador", e)

    try:
        import operator_view
    except Exception as e:
        operator_view = None
        mostrar_error_importacion("operador", e)

    # Configurar la barra lateral
    st.sidebar.title(f"Hola, {st.session_state['full_name']}")
    st.sidebar.caption(f"Rol: {st.session_state['role'].capitalize()}")
    # Selector de tema visual
    theme = st.sidebar.radio("Tema visual", ["Claro", "Oscuro"], index=0, key="theme_selector")
    if theme == "Oscuro":
        st.markdown("""
            <style>
            body, .stApp { background-color: #222 !important; color: #eee !important; }
            </style>
        """, unsafe_allow_html=True)

    # Navegación rápida entre vistas principales
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Navegación rápida")
    nav_option = st.sidebar.radio(
        "Ir a sección:",
        ["Dashboard", "Buscador de Centros", "Creador de Formularios", "Gestión de Áreas", "Gestión de Usuarios", "Revisión de Envíos"],
        key="nav_selector"
    )
    # Guardar la opción seleccionada en session_state para usar en las tabs
    st.session_state["nav_selected"] = nav_option

    # Cargar los datos del CSV (solo lectura)
    @st.cache_data
    def load_csv_data(file_path):
        """Carga el archivo CSV de centros educativos con manejo de errores y codificaciones."""
        try:
            return pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                return pd.read_csv(file_path, encoding='latin-1')
            except Exception as e:
                st.error(f"Error al leer el CSV con codificaciones alternativas: {e}")
                st.info("Verifica que el archivo no esté corrupto.")
                return pd.DataFrame()
        except FileNotFoundError:
            st.error(f"Error: No se encontró el archivo {file_path}")
            st.info("Asegúrate de que 'datos_centros.csv' esté en la carpeta principal del proyecto.")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error inesperado al leer el CSV: {e}")
            st.info("Verifica que el archivo no esté corrupto.")
            return pd.DataFrame()

    with st.spinner("Cargando datos de centros educativos..."):
        df_centros = load_csv_data("datos_centros.csv")

    # Si el DataFrame está vacío después de intentar cargarlo, detenemos la app.
    if df_centros.empty:
        st.warning("No se pudieron cargar los datos de los centros educativos. La app no puede continuar.")
        st.stop()

    # --- ENRUTADOR POR ROL ---
    # Muestra la interfaz correspondiente al rol del usuario
    if st.session_state["role"] == "admin":
        if admin_view:
            admin_view.show_ui(df_centros)
    elif st.session_state["role"] == "operador":
        if operator_view:
            operator_view.show_ui(df_centros)

# --- PUNTO DE ENTRADA PRINCIPAL ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    main_app()
else:
    login_screen()