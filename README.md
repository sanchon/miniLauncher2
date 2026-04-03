# miniLauncher2

Launcher de linea de comandos en Python con:

- comandos definidos en archivo de configuracion (`commands.ini`)
- ejecucion por plantilla (`template`)
- autocompletado en Bash para comandos y parametros

## Uso rapido

Instala dependencias:

```bash
pip install -r requirements.txt
```

1. Ver comandos disponibles:

```bash
python launcher.py --list
```

2. Ejecutar comando (opciones largas estilo Bash):

```bash
python launcher.py deploy --env dev --version 1.2.3
python launcher.py logs --service api --level error
python launcher.py buscar --termino "ejemplo de texto a buscar"
```

3. Modo shell interactivo (sin argumentos):

```bash
python launcher.py
```

Comandos internos en la shell:

- `list`: lista comandos configurados
- `help`: muestra ayuda rapida
- `q` / `exit` / `quit`: salir

En modo interactivo, el historial se guarda en `.launcher_history` para reutilizarlo entre sesiones (navegable con flechas arriba/abajo).

## Estructura del archivo de configuracion (INI)

Cada comando tiene:

- `template`: comando shell que se ejecuta
- `mode`: modo de ejecución (`shell`, `browser`, `open`)
- `params`: nombres de parametros (separados por coma); en la linea de comandos se usan como `--nombre`
- `required`: parametros obligatorios (separados por coma)
- `<param>.choices`: lista de valores sugeridos/validados (separados por coma)

En la CLI: `--param valor` o `--param=valor` (con comillas si lleva espacios).

Ejemplo:

```ini
[deploy]
mode = shell
template = echo Desplegando entorno={env} version={version}
params = env, version
required = env, version
env.choices = dev, staging, prod
```

### Modos de ejecucion

- `shell`: ejecuta la plantilla en shell (como hasta ahora).
- `browser`: abre el resultado de `template` en el navegador por defecto.
- `open`: abre el resultado de `template` con la aplicacion asociada del sistema (fichero, carpeta o URL).

Ejemplos:

```ini
[buscar]
description = Abre una busqueda en el navegador por defecto
mode = browser
template = https://www.google.com/search?q={termino}
params = termino
required = termino

[abrir]
description = Abre fichero o URL con la app asociada
mode = open
template = {ruta}
params = ruta
required = ruta
```

## Activar autocompletado en Bash

### Automatico (recomendado)

Desde el directorio del proyecto (con Python disponible):

```bash
python launcher.py --install-bash-completion
```

Esto añade un bloque marcado a tu `~/.bashrc` (alias `l`, `source` del venv si existe, y `launcher-completion.bash`). Para otro fichero:

```bash
python launcher.py --install-bash-completion --bashrc ~/.profile
```

Para quitar el bloque:

```bash
python launcher.py --uninstall-bash-completion
```

Luego en Git Bash:

```bash
source ~/.bashrc
```

Con el alias activo puedes usar, por ejemplo:

```bash
l --list
l deploy --env dev --version 1.2.3
```

### Manual

Define un alias para llamar al launcher como `l`:

```bash
alias l='python /ruta/a/miniLauncher2/launcher.py'
```

Carga el script de completion:

```bash
source /ruta/a/miniLauncher2/launcher-completion.bash
```

Para dejarlo persistente, agrega ambas lineas a tu `~/.bashrc`.

### Nota para Git Bash en Windows

En Git Bash, lo mas fiable es usar el entorno virtual activado y un alias:

```bash
source .venv/Scripts/activate
alias l='python /c/Users/hsanc/miniLauncher2/launcher.py'
source /c/Users/hsanc/miniLauncher2/launcher-completion.bash
```

Comprobaciones rapidas:

```bash
type -a l
complete -p l
```

Si `complete -p l` muestra `_mini_launcher_complete`, el autocompletado esta registrado.

### Configuracion persistente en ~/.bashrc

Pega este bloque en tu `~/.bashrc`:

```bash
# miniLauncher2
if [ -f /c/Users/hsanc/miniLauncher2/.venv/Scripts/activate ]; then
  source /c/Users/hsanc/miniLauncher2/.venv/Scripts/activate
fi

alias l='python /c/Users/hsanc/miniLauncher2/launcher.py'

if [ -f /c/Users/hsanc/miniLauncher2/launcher-completion.bash ]; then
  source /c/Users/hsanc/miniLauncher2/launcher-completion.bash
fi
```

Recarga la shell:

```bash
source ~/.bashrc
```
