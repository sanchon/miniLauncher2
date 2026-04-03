# Instalacion rapida en Windows (PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "No se encontro 'python' en el PATH. Instala Python 3.10+ desde https://www.python.org/"
    exit 1
}

Write-Host "Creando entorno virtual en .venv ..."
python -m venv .venv

Write-Host "Instalando dependencias y el comando mini-launcher ..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -e "."

Write-Host ""
Write-Host "Listo."
Write-Host "  Activa el venv:  .\.venv\Scripts\Activate.ps1"
Write-Host "  Uso:             mini-launcher --list"
Write-Host "  Shell:           mini-launcher"
Write-Host "  Git Bash (Tab):  mini-launcher --install-bash-completion"
Write-Host ""
