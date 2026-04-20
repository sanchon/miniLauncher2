#!/usr/bin/env zsh
# Genera dist/mini-launcher (un solo fichero) para Linux o macOS.
# Requisitos: pip install pyinstaller
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "Instala PyInstaller: pip install pyinstaller" >&2
  exit 1
fi

pyinstaller --noconfirm --clean --onefile --name mini-launcher launcher.py \
  --add-data "commands.ini:." \
  --add-data "launcher-completion.bash:." \
  --add-data "launcher-completion.ps1:." \
  --add-data "launcher-completion.zsh:." \
  --collect-all prompt_toolkit \
  --collect-all click

echo "Salida: $ROOT/dist/mini-launcher"
echo "Copia junto al binario (si no se generaron solos): commands.ini, launcher-completion.bash, launcher-completion.ps1, launcher-completion.zsh"
