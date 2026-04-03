# miniLauncher2

## Qué es y cómo se usa

Herramienta de línea de órdenes en Python: los comandos se definen en `commands.ini` (plantillas, parámetros `--nombre valor`). Sirve para lanzar acciones, abrir URLs o ficheros según comandos que tú mismo configuras.

Minilauncher permite que esos comandos inventados por ti tengan autocompletado en bash, en powershell, o en el propio minilauncher (tiene modo shell)

**Ejemplos** (con el entorno ya instalado y activado):

```text
mini-launcher --list
mini-launcher deploy --env dev --version 1.0
mini-launcher
```

Sin argumentos entra en una shell interactiva; dentro: `list`, `help`, `q` para salir.

---

## Instalación desde cero

1. Instala **Python 3.10+** y clona o descarga este proyecto.

2. En la carpeta del proyecto:

   - **Windows (PowerShell):** `.\install.ps1`
   - **Linux / macOS:** `chmod +x install.sh && ./install.sh`

3. Activa el entorno virtual:

   - PowerShell: `.\.venv\Scripts\Activate.ps1`
   - Bash: `source .venv/bin/activate`

4. Comprueba: `mini-launcher --list`

**Opcional — autocompletado con Tab:** `mini-launcher --install-bash-completion` (Git Bash) o `mini-launcher --install-powershell-completion` (PowerShell); luego recarga la terminal o el perfil.
