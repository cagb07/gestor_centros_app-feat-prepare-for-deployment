import streamlit as st
import pandas as pd
import database
import auth
import admin_view
import operator_view

# Configuración de la página (¡llamarla primero!)
st.set_page_config(page_title="Gestor de Centros", layout="wide", initial_sidebar_state="collapsed")

# --- FUNCIÓN DE LOGIN ---
def login_screen():
    st.title("Gestor de Centros Educativos 🇨🇷")
    st.header("Inicio de Sesión")

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

    if submitted:
        user_data = database.get_user(username)
        
        if user_data and auth.check_password(password, user_data["password_hash"]):
            # Login exitoso
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = user_data["id"]
            st.session_state["username"] = user_data["username"]
            st.session_state["role"] = user_data["role"]
            st.session_state["full_name"] = user_data["full_name"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# --- APLICACIÓN PRINCIPAL (POST-LOGIN) ---
def main_app():
    # Configurar la barra lateral
    st.sidebar.title(f"Hola, {st.session_state['full_name']}")
    st.sidebar.caption(f"Rol: {st.session_state['role'].capitalize()}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()
    
    st.sidebar.divider()
    
    # Cargar los datos del CSV (solo lectura)
    @st.cache_data
    def load_csv_data(file_path):
        try:
            # Intentar con UTF-8, que es el estándar más común.
            return pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # Si UTF-8 falla, intentar con Latin-1, que es común en Europa/América.
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

    df_centros = load_csv_data("datos_centros.csv")

    # Si el DataFrame está vacío después de intentar cargarlo, detenemos la app.
    if df_centros.empty:
        st.warning("No se pudieron cargar los datos de los centros educativos. La app no puede continuar.")
        st.stop()

    # --- ENRUTADOR POR ROL ---
    # Muestra la interfaz correspondiente al rol del usuario
    if st.session_state["role"] == "admin":
        admin_view.show_ui(df_centros)
        
    elif st.session_state["role"] == "operador":
        operator_view.show_ui(df_centros)

# --- PUNTO DE ENTRADA PRINCIPAL ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    main_app()
else:
    login_screen()