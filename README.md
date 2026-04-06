# miniLauncher2

Launcher de comandos personalizados para terminal. Define tus comandos en un fichero INI, ejecútalos con `--param valor`, y usa **Tab** para autocompletar en Bash, PowerShell o la shell interactiva incluida.

Ideal para acortar tareas repetitivas (despliegues, abrir URLs, lanzar herramientas) con una interfaz coherente y sin escribir scripts a cada ruta.

[![Demo](https://asciinema.org/a/N44JIajcRdYkMggo.svg)](https://asciinema.org/a/N44JIajcRdYkMggo)

---

## Instalación (binario portable)

1. Descarga el ejecutable para tu plataforma desde la [página de releases](../../releases).
2. Coloca en la **misma carpeta** que el binario estos ficheros (ya incluidos en el release):
   - `commands.ini` — tu configuración de comandos
   - `launcher-completion.bash` y `launcher-completion.ps1` — scripts de autocompletado
3. **Activa el autocompletado** (opcional):
   - Git Bash: `./mini-launcher --install-bash-completion`, luego reinicia la terminal.
   - PowerShell: `./mini-launcher --install-powershell-completion`, luego `. $PROFILE`.

---

## Guía de uso

### Listar los comandos disponibles

```text
mini-launcher --list
```

### Ejecutar un comando

Los parámetros se pasan como opciones largas:

```text
mini-launcher deploy --env dev --version 1.0
mini-launcher buscar --termino "python asyncio"
```

### Shell interactiva

Sin argumentos se abre un prompt `l>` con historial persistente y Tab:

```text
mini-launcher
```

Dentro: `list` para ver comandos, `help` para ayuda, `q` o `exit` para salir.

### Cómo se ve el autocompletado

```
l> dep█
       └─ Tab → completa el nombre del comando
l> deploy █
       └─ Tab → ofrece --env=  --version=  …
l> deploy --env█
       └─ Tab → si hay choices: dev, staging, prod …
l> deploy --env=dev --version=1.0█
```

La misma lógica funciona en **Git Bash** y **PowerShell** tras instalar los scripts de completado.

### Usar un fichero de configuración alternativo

```text
mini-launcher --config /ruta/mi_config.ini deploy --env prod
```

---

## Referencia de `commands.ini`

Toda la documentación sobre los modos (`shell`, `browser`, `open`, `exec`), parámetros, `choices`, `path`, `detach` y ejemplos está en:

**[docs/configuracion-ini.md](docs/configuracion-ini.md)**

---

## Construcción del binario (desarrolladores)

```text
pip install ".[build]"
```

- **Windows:** `.\scripts\build_windows.ps1`
- **Linux / macOS:** `chmod +x scripts/build_unix.sh && ./scripts/build_unix.sh`

El resultado queda en `dist/mini-launcher` (o `.exe` en Windows).

El workflow [`.github/workflows/release.yml`](.github/workflows/release.yml) compila en paralelo para Windows, Linux y macOS al hacer push de un tag `vX.Y.Z`.