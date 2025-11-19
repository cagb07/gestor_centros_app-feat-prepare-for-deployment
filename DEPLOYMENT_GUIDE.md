# Guía de Despliegue en Streamlit Community Cloud

Esta guía te llevará paso a paso para desplegar tu aplicación "Gestor de Centros Educativos" en la nube de Streamlit, usando GitHub.

### Paso 1: Preparar tu Código Localmente

Antes de subir tu código, asegúrate de tener la estructura correcta y de no incluir archivos sensibles.

1.  **Verifica tu `.gitignore`:** Asegúrate de que este archivo exista en la raíz de tu proyecto y que contenga la línea `.streamlit/secrets.toml`. Esto es **muy importante** para no subir tu contraseña de la base de datos a un repositorio público.
2.  **Verifica `requirements.txt`:** Asegúrate de que todas las librerías que tu proyecto necesita están listadas en este archivo.

### Paso 2: Crear un Repositorio en GitHub

1.  **Ve a GitHub:** Inicia sesión en tu cuenta de [GitHub](https://github.com).
2.  **Crea un Nuevo Repositorio:**
    *   Haz clic en el botón verde "New" (Nuevo).
    *   Dale un nombre a tu repositorio (ej: `gestor-centros-app`).
    *   **Importante:** Asegúrate de que el repositorio sea **Público**. Streamlit Community Cloud requiere esto para poder acceder al código.
    *   No inicialices el repositorio con un `README` o `.gitignore` (ya que los tenemos localmente).
    *   Haz clic en "Create repository".

### Paso 3: Subir tu Código al Repositorio

GitHub te mostrará unas instrucciones. Sigue la sección que dice **"...or push an existing repository from the command line"**.

Abre tu terminal (como PowerShell, Git Bash, etc.) en la carpeta de tu proyecto y ejecuta los siguientes comandos, **reemplazando la URL con la de tu propio repositorio**:

```bash
# Inicializa Git en tu carpeta local (si no lo has hecho)
git init

# Añade todos tus archivos al área de preparación
git add .

# Crea tu primer "commit" (una instantánea de tu código)
git commit -m "Versión inicial del proyecto"

# Define la rama principal como "main"
git branch -M main

# Conecta tu repositorio local con el de GitHub
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git

# Sube tu código a GitHub
git push -u origin main
```

### Paso 4: Desplegar en Streamlit Community Cloud

1.  **Ve a Streamlit Community Cloud:** Inicia sesión con tu cuenta de GitHub en [share.streamlit.io](https://share.streamlit.io/).
2.  **Crea una Nueva App:**
    *   Haz clic en el botón "New app".
    *   **Repositorio:** Selecciona el repositorio que acabas de crear.
    *   **Rama (Branch):** Asegúrate de que esté seleccionada la rama `main`.
    *   **Archivo Principal (Main file path):** Escribe `app.py`.
    *   Haz clic en el botón "Advanced settings...".

3.  **Configurar los Secretos (¡Paso Clave!):**
    *   En la sección de "Secrets", pegarás el contenido de tu archivo local `.streamlit/secrets.toml`.
    *   El contenido debería ser algo así:

      ```toml
      DB_URL = "postgresql://neondb_owner:xxxxxxxx@ep-green-darkness-ahkr8bxz.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
      ```

    *   Copia y pega esa línea en el cuadro de texto de "Secrets".

4.  **Desplegar:**
    *   Haz clic en el botón "Deploy!".

Streamlit comenzará a construir tu aplicación. Verás un registro de la instalación de las dependencias. Después de unos minutos, ¡tu aplicación estará en línea y accesible para todo el mundo!

### Paso 5: ¡Listo!

Una vez que el despliegue termine, serás redirigido a la URL pública de tu nueva aplicación. ¡Felicidades, has desplegado tu proyecto!
