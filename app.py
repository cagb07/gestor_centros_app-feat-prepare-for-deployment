import streamlit as st
import pandas as pd
import database

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