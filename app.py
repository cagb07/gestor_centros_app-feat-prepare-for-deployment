
import streamlit as st
import pandas as pd
import database
import auth

# Configuración de la página (debe ejecutarse antes de otros comandos de Streamlit)
try:
    st.set_page_config(page_title="Gestor de Centros Educativos", layout="wide")
except Exception:
    # Si ya se llamó anteriormente, ignorar el error
    pass

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
    st.sidebar.title(f"Hola, {st.session_state.get('full_name', 'Usuario')}")
    st.sidebar.caption(f"Rol: {st.session_state.get('role', 'desconocido').capitalize()}")

    # Selector de tema visual
    theme = st.sidebar.radio("Tema visual", ["Claro", "Oscuro"], index=0, key="theme_selector")

    def apply_theme_css(selected_theme: str):
        """Aplica CSS que fuerza estilos para tema claro u oscuro.
        Usamos selectores generales y !important para sobreescribir estilos de Streamlit.
        """
        if selected_theme == "Oscuro":
            css = """
            <style>
            :root { color-scheme: dark; }
            /* Áreas principales */
            .stApp, .main, .block-container, .css-1d391kg { background-color: #111 !important; color: #e6e6e6 !important; }
            /* Sidebar */
            .css-1d391kg, .css-1v3fvcr { background-color: #0f0f0f !important; color: #e6e6e6 !important; }
            /* Texto y títulos */
            .stText, .stMarkdown, .stHeader, h1, h2, h3, h4 { color: #e6e6e6 !important; }
            /* Botones */
            button, .stButton>button { background-color:#333 !important; color:#fff !important; }
            /* Tablas */
            table { color: #e6e6e6 !important; }
            </style>
            """
        else:
            css = """
            <style>
            :root { color-scheme: light; }
            .stApp, .main, .block-container, .css-1d391kg { background-color: #ffffff !important; color: #111 !important; }
            .css-1d391kg, .css-1v3fvcr { background-color: #ffffff !important; color: #111 !important; }
            button, .stButton>button { background-color: initial !important; color: initial !important; }
            </style>
            """
        st.markdown(css, unsafe_allow_html=True)

    # Aplicar el CSS del tema seleccionado
    try:
        apply_theme_css(theme)
    except Exception:
        # No crítico; continuar sin bloquear la app
        pass

    # Navegación rápida entre vistas principales
    st.sidebar.markdown("---")

    # Mostrar la vista correspondiente según el rol
    if st.session_state.get("role") == "admin" and admin_view:
        # Cargar datos de centros
        try:
            df_centros = pd.read_csv("datos_centros.csv")
        except Exception as e:
            st.error(f"Error cargando datos de centros: {e}")
            df_centros = pd.DataFrame()
        admin_view.show_ui(df_centros)
    elif st.session_state.get("role") == "operador" and operator_view:
        try:
            df_centros = pd.read_csv("datos_centros.csv")
        except Exception as e:
            st.error(f"Error cargando datos de centros: {e}")
            df_centros = pd.DataFrame()
        operator_view.show_ui(df_centros)
    else:
        st.error("No se pudo determinar la vista para el usuario actual.")


# --- FLUJO DE AUTENTICACIÓN Y ENRUTAMIENTO PRINCIPAL ---
def login_form():
    st.title("Gestor de Centros Educativos")
    st.subheader("Iniciar sesión")
    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar sesión")
    if submit:
        # Verificar conexión a la base de datos antes de intentar autenticar
        conn_test = database.get_db_connection()
        if conn_test is None:
            st.error("Error: no hay conexión a la base de datos. Revisa la variable DB_URL o la configuración de la BD.")
            return
        user = database.get_user(username)
        if user and auth.check_password(password, user["password_hash"]):
            st.session_state["user_id"] = user["id"]
            st.session_state["username"] = user["username"]
            st.session_state["full_name"] = user["full_name"]
            st.session_state["role"] = user["role"]
            st.success("¡Bienvenido, {}!".format(user["full_name"]))
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

def logout_button():
    if st.sidebar.button("Cerrar sesión", key="logout_btn"):
        st.session_state.clear()
        st.rerun()


# --- PUNTO DE ENTRADA DE LA APP ---
def main():
    st.set_page_config(page_title="Gestor de Centros Educativos", layout="wide")
    if "role" in st.session_state:
        logout_button()
        main_app()
    else:
        login_form()


if __name__ == "__main__":
    main()
else:
    main()