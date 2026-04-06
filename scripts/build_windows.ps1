# Genera dist\mini-launcher.exe (un solo fichero) para Windows.
# Requisitos: pip install pyinstaller
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Error "Instala PyInstaller: pip install pyinstaller"
    exit 1
}

# En PowerShell hay que entrecomillar el argumento por el carácter ';'.
& pyinstaller --noconfirm --clean --onefile --name mini-launcher launcher.py `
    '--add-data=commands.ini;.' `
    '--add-data=launcher-completion.bash;.' `
    '--add-data=launcher-completion.ps1;.' `
    --collect-all prompt_toolkit `
    --collect-all click

Write-Host "Salida: $Root\dist\mini-launcher.exe"
Write-Host "Copia junto al .exe (si no se generaron solos): commands.ini, launcher-completion.bash, launcher-completion.ps1"
