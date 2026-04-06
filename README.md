# miniLauncher2

**Tu propio launcher de terminal, sin escribir scripts a cada ruta.**

Define comandos en un fichero de configuración, ejecútalos con opciones al estilo `--param valor`, y usa **Tab** donde quieras: Bash, PowerShell o la shell interactiva incluida. Ideal para acortar tareas repetitivas (despliegues, abrir URLs, lanzar herramientas) con una interfaz coherente.

---

## Qué ofrece

| | |
|--|--|
| **Configuración clara** | Comandos y plantillas en `commands.ini` — sin recompilar nada. |
| **Varios modos** | Shell, navegador, abrir con la app del sistema, o **lanzar un .exe/proceso** con argumentos (`exec`). |
| **Autocompletado** | Misma lógica para Git Bash, PowerShell y el modo interactivo (`prompt_toolkit`). |
| **Shell propia** | `mini-launcher` sin argumentos → prompt `l>`, historial persistente, salida con `q`. |

**Ejemplos** (tras instalar y activar el entorno virtual):

```text
mini-launcher --list
mini-launcher deploy --env dev --version 1.0
mini-launcher
```

La última línea abre la shell interactiva; dentro: `list`, `help`; `q` o `exit` para salir.

### Cómo se ve el autocompletado (simulación)

No hace falta grabar un vídeo: en la shell interactiva (`mini-launcher` sin argumentos) el **Tab** va rellenando por pasos lo que definiste en `commands.ini`. El símbolo **█** marca dónde está el cursor:

```
 ╭─ miniLauncher · shell interactiva ─────────────────╮
 │ l> dep█                                            │
 │      └─ Tab → completa el nombre del comando       │
 │ l> deploy █                                        │
 │      └─ Tab → ofrece --env=  --version=  …         │
 │ l> deploy --env█                                   │
 │      └─ Tab → si hay choices: dev, staging, prod … │
 │ l> deploy --env=dev --version=1.0█                 │
 ╰────────────────────────────────────────────────────╯
```

Misma idea en **Git Bash** o **PowerShell** (después de `--install-bash-completion` / `--install-powershell-completion`): escribes `l deploy ...` o `mini-launcher deploy ...` y Tab recorre comandos y opciones al mismo estilo.

**Grabación real (GIF o asciinema):** pasos en [docs/grabar-demo.md](docs/grabar-demo.md).

---

## Instalación en cuatro pasos

1. **Python 3.10+** instalado; clona o descarga este repositorio.

2. Desde la raíz del proyecto:
   - **Windows:** `.\install.ps1`
   - **Linux / macOS:** `chmod +x install.sh && ./install.sh`

3. **Activa el virtualenv**
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
   - Bash: `source .venv/bin/activate`

4. **Prueba:** `mini-launcher --list`

**Opcional:** autocompletado con Tab — `mini-launcher --install-bash-completion` (Git Bash) o `mini-launcher --install-powershell-completion`; después recarga la terminal o ejecuta `. $PROFILE` en PowerShell.

---

## Documentación

| Recurso | Contenido |
|---------|-----------|
| [docs/configuracion-ini.md](docs/configuracion-ini.md) | Referencia del INI: `[mini-launcher]`, `template`, `mode`, `executable` / `arguments` (`exec` y `browser`), `detach`, `params`, `required`, `*.choices`, `*.path`, sustitución y ejemplos. |
| [docs/grabar-demo.md](docs/grabar-demo.md) | Cómo grabar un GIF o un cast de asciinema para el README. |
