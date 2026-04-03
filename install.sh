#!/usr/bin/env bash
# Instalacion rapida en Linux / macOS / Git Bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontro python3 en el PATH." >&2
  exit 1
fi

echo "Creando entorno virtual en .venv ..."
python3 -m venv .venv

echo "Instalando dependencias y el comando mini-launcher ..."
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/pip install -e "."

echo ""
echo "Listo."
echo "  Activa el venv:  source .venv/bin/activate"
echo "  Uso:             mini-launcher --list"
echo "  Shell:           mini-launcher"
echo "  Git Bash (Tab):  mini-launcher --install-bash-completion"
echo ""
