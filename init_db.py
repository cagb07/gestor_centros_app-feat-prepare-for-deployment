import os
import sys

try:
    import psycopg2
except ImportError:
    print("=" * 50)
    print("❌ ERROR: Dependencia 'psycopg2' no encontrada.")
    print("Por favor, instala las dependencias del proyecto ejecutando:")
    print("\npip install -r requirements.txt\n")
    print("Asegúrate de tener tu entorno virtual activado.")
    print("=" * 50)
    sys.exit(1)

# 1. Cargar configuración MANUALMENTE para evitar errores de Streamlit
print("--- INICIALIZADOR DE BASE DE DATOS ---")

db_url = None
secrets_path = os.path.join(".streamlit", "secrets.toml")

# Intentar leer el archivo secrets.toml línea por línea
if os.path.exists(secrets_path):
    print(f"Leyendo secretos desde {secrets_path}...")
    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            for line in f:
                if "DB_URL" in line and "=" in line:
                    parts = line.split("=", 1)
                    clean_url = parts[1].strip().strip('"').strip("'")
                    db_url = clean_url
                    break
        if not db_url:
            print(f"⚠️  No se encontró la línea 'DB_URL' en {secrets_path}")
    except Exception as e:
        print(f"❌ Error leyendo secrets.toml: {e}")
else:
    print(f"⚠️  No se encontró el archivo {secrets_path}")
    print("Asegúrate de estar en la carpeta raíz del proyecto.")

# Si no se encontró en el archivo, preguntar al usuario
if not db_url:
    print("\n❌ No se pudo detectar la DB_URL automáticamente.")
    print("Por favor, pega tu Connection String de PostgreSQL aquí (ej: postgresql://user:pass@host/db):")
    db_url = input("> ").strip()

if not db_url or db_url == "REEMPLAZA_CON_TU_CONNECTION_STRING_DE_POSTGRESQL":
    print("❌ Error: Se requiere una DB_URL válida para continuar.")
    print("Edita tu archivo .streamlit/secrets.toml y reemplaza el placeholder.")
    sys.exit(1)

# Establecer la variable de entorno para que database.py la use
os.environ["DB_URL"] = db_url

# 2. Ahora sí importar la base de datos (después de configurar el entorno)
try:
    import database
except ImportError as e:
    print(f"❌ Error importando database.py: {e}")
    sys.exit(1)
except SyntaxError as e:
    print(f"❌ Error de sintaxis en database.py: {e}")
    sys.exit(1)

# 3. Ejecutar la inicialización
def run_init():
    try:
        print("\nConectando a la base de datos...")
        # La conexión se prueba aquí al crear las tablas
        database.create_tables()
        print("✅ ¡Conexión exitosa y tablas creadas!")
    
    except psycopg2.OperationalError as e:
        print("="*50)
        print("❌ ¡ERROR DE CONEXIÓN A LA BASE DE DATOS!")
        print(f"\nDetalle: {e}")
        print("\nPOSIBLES SOLUCIONES:")
        print("1. ¿La 'Connection String' en .streamlit/secrets.toml es correcta?")
        print("2. ¿La base de datos (Neon) está encendida y no 'dormida'?")
        print("3. (LA MÁS PROBABLE) ¿Agregaste tu dirección IP pública a la 'IP Allow List' en Neon?")
        print("="*50)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado al conectar: {e}")
        sys.exit(1)

    # Crear usuario admin
    admin_user = "admin"
    admin_pass = "Admin1234" # Puedes cambiar esta contraseña
    admin_name = "Administrador Principal"
    
    print(f"\nCreando/Verificando usuario '{admin_user}'...")
    database.create_admin_user(admin_user, admin_pass, admin_name)
    
    print("\n✅ ¡Inicialización completada con éxito!")
    print(f"Usuario: {admin_user}")
    print(f"Pass: {admin_pass}")
    print("\nAhora ejecuta: streamlit run app.py")

if __name__ == "__main__":
    run_init()