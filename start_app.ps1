<#
start_app.ps1

Script de inicialización para Windows (PowerShell).
Acciones:
- Crea un virtualenv `.venv` usando Python 3.11 si está disponible, si no usa `python` por defecto.
- Activa el venv
- Actualiza `pip` e instala `requirements.txt`
- Ejecuta `init_db.py` para crear tablas y admin
- Lanza `streamlit run app.py`

Uso (desde la carpeta del proyecto):
    powershell -ExecutionPolicy Bypass -File .\start_app.ps1

Opcional: para recrear el venv y forzar reinstalación:
    powershell -ExecutionPolicy Bypass -File .\start_app.ps1 -Recreate
#>

param(
    [switch]$Recreate
)

set -e

Write-Host "== Inicializando aplicación: gestor_centros_app ==" -ForegroundColor Cyan

if ($Recreate -and (Test-Path -Path ".venv")) {
    Write-Host "Recreando entorno virtual: eliminando .venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .venv
}

if (!(Test-Path -Path ".venv")) {
    Write-Host "Creando entorno virtual (.venv) usando Python 3.11 si está disponible..." -ForegroundColor Green
    $created = $false
    try {
        & py -3.11 -m venv .venv
        if ($LASTEXITCODE -eq 0) { $created = $true; Write-Host "Entorno creado con py -3.11" -ForegroundColor Green }
    } catch {
        # ignorar
    }

    if (-not $created) {
        Write-Host "Python 3.11 no disponible con el launcher. Intentando 'python -m venv .venv'..." -ForegroundColor Yellow
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) {
            Write-Error "No se pudo crear el entorno virtual. Asegúrate de tener Python instalado y accesible desde 'py' o 'python'."
            exit 1
        }
    }
} else {
    Write-Host "Se detectó .venv existente. Usando el entorno existente." -ForegroundColor Yellow
}

Write-Host "Activando entorno virtual..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Error "No se pudo activar el entorno virtual (.venv). Comprueba permisos de ejecución de PowerShell o ejecuta manualmente: & .\\.venv\\Scripts\\Activate.ps1"
    exit 1
}

Write-Host "Actualizando pip e instalando dependencias (requirements.txt)..." -ForegroundColor Green
python -m pip install --upgrade pip
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error instalando dependencias. Revisa la salida anterior para detalles."
    exit 1
}

Write-Host "Ejecutando init_db.py para crear tablas y admin..." -ForegroundColor Green
python init_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "init_db.py falló. Revisa la salida anterior."
    exit 1
}

Write-Host "Arrancando Streamlit (app.py)..." -ForegroundColor Green
streamlit run app.py
