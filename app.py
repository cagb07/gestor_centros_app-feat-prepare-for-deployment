
import streamlit as st
import pandas as pd
import database
import auth

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
    if theme == "Oscuro":
        st.markdown("""
            <style>
            body, .stApp { background-color: #222 !important; color: #eee !important; }
            /* ...estilos personalizados... */
            </style>
        """, unsafe_allow_html=True)

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
        user = database.get_user(username)
        if user and auth.check_password(password, user["password_hash"]):
            st.session_state["user_id"] = user["id"]
            st.session_state["username"] = user["username"]
            st.session_state["full_name"] = user["full_name"]
            st.session_state["role"] = user["role"]
            st.success("¡Bienvenido, {}!".format(user["full_name"]))
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

def logout_button():
    if st.sidebar.button("Cerrar sesión", key="logout_btn"):
        st.session_state.clear()
        st.experimental_rerun()


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