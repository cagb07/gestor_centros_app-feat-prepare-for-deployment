try:
    import streamlit as st
except Exception:
    # Si Streamlit no está instalado (por ejemplo al ejecutar init_db.py),
    # creamos un objeto 'st' mínimo con lo necesario para que el módulo
    # no falle en imports y para permitir uso en scripts CLI.
    class _DummyStreamlit:
        def __init__(self):
            self.secrets = {}

        def warning(self, *args, **kwargs):
            print("WARNING:", *args)

        def error(self, *args, **kwargs):
            print("ERROR:", *args)

        def stop(self, *args, **kwargs):
            raise SystemExit()

        # Proveer decorator no-op para cache_resource
        def cache_resource(self, *c_args, **c_kwargs):
            # Allow use both as @st.cache_resource and @st.cache_resource(...)
            if len(c_args) == 1 and callable(c_args[0]) and not c_kwargs:
                return c_args[0]

            def _decorator(f):
                return f

            return _decorator

    st = _DummyStreamlit()
import psycopg2
import pandas as pd
import json
import os

# --- CONEXIÓN PRINCIPAL ---

@st.cache_resource
def get_db_connection():
    """
    Se conecta a la base de datos Postgres.
    Intenta leer de st.secrets primero, luego de variables de entorno.
    """
    db_url = None
    
    # 1. Intentar leer de secretos de Streamlit (cuando la app corre)
    try:
        if "DB_URL" in st.secrets:
            db_url = st.secrets["DB_URL"]
    except Exception:
        pass # st.secrets no existe en el script init_db
    
    # 2. Si falla, intentar leer de variables de entorno (para init_db.py)
    if not db_url:
        db_url = os.environ.get("DB_URL")

    if not db_url:
        # Si no hay DB_URL, no abortamos la ejecución de la app.
        # En lugar de detener la app, devolvemos None y el resto
        # de funciones manejarán la ausencia de conexión de forma segura.
        try:
            st.warning("⚠️ Aviso: No se encontró DB_URL en secrets.toml ni en variables de entorno. Algunas funcionalidades dependerán de la base de datos y estarán deshabilitadas.")
        except Exception:
            # En contextos fuera de Streamlit (scripts) st.warning puede fallar
            print("⚠️ Aviso: No se encontró DB_URL en secrets.toml ni en variables de entorno.")
        return None

    # Dejamos que el error se propague si la conexión falla
    conn = psycopg2.connect(db_url)
    return conn

# --- INICIALIZACIÓN ---

def create_tables():
    """Crea todas las tablas de la app si no existen."""
    conn = get_db_connection()
    if not conn:
        print("⚠️ Omisión de creación de tablas: no hay conexión a la BD (DB_URL no configurada).")
        return

    try:
        with conn.cursor() as cur:
            # Tabla de Centros Educativos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS centros (
                    id SERIAL PRIMARY KEY,
                    codigo VARCHAR(20) UNIQUE,
                    nombre VARCHAR(255) NOT NULL,
                    provincia VARCHAR(100),
                    otros_campos JSONB
                );
            """)
            # Tabla de auditoría
            cur.execute("""
                CREATE TABLE IF NOT EXISTS auditoria (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES usuarios(id),
                    accion VARCHAR(100) NOT NULL,
                    detalle TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Tabla de Áreas
            cur.execute("""
                CREATE TABLE IF NOT EXISTS form_areas (
                    id SERIAL PRIMARY KEY,
                    area_name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT
                );
            """)
            
            # Tabla de Usuarios (con reseteo)
            cur.execute("DROP TABLE IF EXISTS usuarios CASCADE;")
            cur.execute("""
                CREATE TABLE usuarios (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'operador')),
                    full_name VARCHAR(100),
                    failed_attempts INTEGER DEFAULT 0,
                    is_locked BOOLEAN DEFAULT FALSE
                );
            """)
            
            # Tabla de Plantillas
            cur.execute("""
                CREATE TABLE IF NOT EXISTS form_templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    structure JSONB NOT NULL,
                    created_by_user_id INTEGER REFERENCES usuarios(id),
                    area_id INTEGER REFERENCES form_areas(id)
                );
            """)
            
            # Tabla de Envíos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS form_submissions (
                    id SERIAL PRIMARY KEY,
                    template_id INTEGER REFERENCES form_templates(id),
                    user_id INTEGER REFERENCES usuarios(id),
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.commit()
        print("✅ Tablas verificadas/creadas exitosamente.")
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
    # NOTA: NO HAY 'conn.close()' AQUÍ. ES INTENCIONAL.

# --- FUNCIONES DE USUARIO ---

def get_user(username):
    conn = get_db_connection()
    if not conn:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT id, username, password_hash, role, full_name, failed_attempts, is_locked FROM usuarios WHERE username = %s", (username,))
        user_data = cur.fetchone()
    # Sin conn.close()
    if user_data:
        return {
            "id": user_data[0],
            "username": user_data[1],
            "password_hash": user_data[2],
            "role": user_data[3],
            "full_name": user_data[4],
            "failed_attempts": user_data[5],
            "is_locked": user_data[6]
        }
    return None

def increment_failed_attempts(username):
    conn = get_db_connection()
    if not conn:
        return
    with conn.cursor() as cur:
        cur.execute("UPDATE usuarios SET failed_attempts = failed_attempts + 1 WHERE username = %s", (username,))
        cur.execute("SELECT failed_attempts FROM usuarios WHERE username = %s", (username,))
        attempts = cur.fetchone()[0]
        if attempts >= 5:
            cur.execute("UPDATE usuarios SET is_locked = TRUE WHERE username = %s", (username,))
    conn.commit()

def reset_failed_attempts(username):
    conn = get_db_connection()
    if not conn:
        return
    with conn.cursor() as cur:
        cur.execute("UPDATE usuarios SET failed_attempts = 0 WHERE username = %s", (username,))
    conn.commit()

def unlock_user(user_id):
    conn = get_db_connection()
    if not conn:
        return False, "No hay conexión a la base de datos."
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET is_locked = FALSE, failed_attempts = 0 WHERE id = %s", (user_id,))
        conn.commit()
        return True, "Usuario desbloqueado."
    except Exception as e:
        conn.rollback()
        return False, f"Error al desbloquear usuario: {e}"

def create_admin_user(username, password, full_name):
    from auth import hash_password
    hashed = hash_password(password)
    conn = get_db_connection()
    if not conn:
        print("⚠️ No se pudo crear admin: no hay conexión a la BD.")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO usuarios (username, password_hash, role, full_name) VALUES (%s, %s, 'admin', %s)", (username, hashed, full_name))
        conn.commit()
        print(f"✅ Usuario admin '{username}' creado.")
    except psycopg2.IntegrityError:
        conn.rollback()
        print(f"⚠️  Usuario admin '{username}' ya existe. No se creó de nuevo.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creando admin: {e}")
    # Sin conn.close()

def create_user(username, password, role, full_name):
    from auth import hash_password
    hashed = hash_password(password)
    conn = get_db_connection()
    if not conn:
        return False, "No hay conexión a la base de datos."
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO usuarios (username, password_hash, role, full_name) VALUES (%s, %s, %s, %s)", (username, hashed, role, full_name))
        conn.commit()
        return True, "Usuario creado."
    except psycopg2.IntegrityError:
        conn.rollback()
        return False, "El usuario ya existe."
    # Sin conn.close()

def change_user_password(user_id, new_password):
    """Actualiza la contraseña de un usuario dado su id."""
    from auth import hash_password
    hashed = hash_password(new_password)
    conn = get_db_connection()
    if not conn:
        return False, "No hay conexión a la base de datos."
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE usuarios SET password_hash = %s WHERE id = %s", (hashed, user_id))
        conn.commit()
        return True, "Contraseña actualizada." 
    except Exception as e:
        conn.rollback()
        return False, f"Error al actualizar contraseña: {e}"

def get_all_users():
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame(columns=["id", "username", "role", "full_name"])
    df = pd.read_sql("SELECT id, username, role, full_name FROM usuarios ORDER BY full_name", conn)
    return df

# --- FUNCIONES DE ÁREAS Y TEMPLATES ---

def create_area(area_name, description):
    conn = get_db_connection()
    if not conn:
        return False, "No hay conexión a la base de datos."
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO form_areas (area_name, description) VALUES (%s, %s)", (area_name, description))
        conn.commit()
        return True, "Área creada."
    except psycopg2.IntegrityError:
        conn.rollback()
        return False, "El nombre de área ya existe."
    # Sin conn.close()

def get_all_areas():
    conn = get_db_connection()
    if not conn:
        return []
    with conn.cursor() as cur:
        cur.execute("SELECT id, area_name, description FROM form_areas ORDER BY area_name")
        data = [{"id": a[0], "name": a[1], "description": a[2]} for a in cur.fetchall()]
    return data

def save_form_template(name, structure, user_id, area_id):
    conn = get_db_connection()
    if not conn:
        raise RuntimeError("No hay conexión a la base de datos.")
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO form_templates (name, structure, created_by_user_id, area_id) VALUES (%s, %s, %s, %s)",
                        (name, json.dumps(structure), user_id, area_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    # Sin conn.close()

def get_templates_by_area(area_id):
    conn = get_db_connection()
    if not conn:
        return []
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM form_templates WHERE area_id = %s ORDER BY name", (area_id,))
        data = [{"id": t[0], "name": t[1]} for t in cur.fetchall()]
    return data

def get_template_structure(template_id):
    conn = get_db_connection()
    if not conn:
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT structure FROM form_templates WHERE id = %s", (template_id,))
        res = cur.fetchone()
    return res[0] if res else None

# --- FUNCIONES DE ENVÍOS Y DASHBOARD ---

def save_submission(template_id, user_id, data):
    conn = get_db_connection()
    if not conn:
        raise RuntimeError("No hay conexión a la base de datos.")
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO form_submissions (template_id, user_id, data) VALUES (%s, %s, %s)",
                        (template_id, user_id, json.dumps(data, default=str)))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    # Sin conn.close()

def get_submissions_by_user(user_id):
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame(columns=["id", "name", "created_at", "data"])
    df = pd.read_sql("""
        SELECT s.id, t.name, s.created_at, s.data FROM form_submissions s 
        JOIN form_templates t ON s.template_id = t.id WHERE s.user_id = %s ORDER BY s.created_at DESC
    """, conn, params=(user_id,))
    return df

def get_total_submission_count():
    conn = get_db_connection()
    if not conn:
        return 0
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM form_submissions")
        count = cur.fetchone()[0]
    return count

def get_submission_count_by_area():
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame(columns=["area_name", "submission_count"])
    df = pd.read_sql("""
        SELECT a.area_name, COUNT(s.id) as submission_count
        FROM form_submissions s
        JOIN form_templates t ON s.template_id = t.id
        JOIN form_areas a ON t.area_id = a.id
        GROUP BY a.area_name
        ORDER BY submission_count DESC
    """, conn)
    return df

def get_submission_count_by_user():
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame(columns=["full_name", "submission_count"])
    df = pd.read_sql("""
        SELECT u.full_name, COUNT(s.id) as submission_count
        FROM form_submissions s
        JOIN usuarios u ON s.user_id = u.id
        GROUP BY u.full_name
        ORDER BY submission_count DESC
    """, conn)
    return df

def get_all_submissions_with_details():
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame(columns=["id", "user_name", "template_name", "area_name", "created_at"])
    df = pd.read_sql("""
        SELECT s.id, u.full_name as user_name, t.name as template_name, a.area_name, s.created_at
        FROM form_submissions s
        JOIN usuarios u ON s.user_id = u.id
        JOIN form_templates t ON s.template_id = t.id
        JOIN form_areas a ON t.area_id = a.id
        ORDER BY s.created_at DESC
    """, conn)
    return df