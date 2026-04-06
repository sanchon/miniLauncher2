# Referencia del fichero de configuración (`commands.ini`)

miniLauncher2 lee un único fichero **INI** (por defecto `commands.ini` en el mismo directorio que `launcher.py`). Puedes usar otro con:

```text
mini-launcher --config C:\ruta\mi_config.ini ...
```

Codificación recomendada: **UTF-8**.

---

## Estructura general

- Cada **sección** `[nombre]` define **un comando lógico**. El `nombre` es el que escribes en la terminal (`deploy`, `logs`, etc.). Debe ser una sola palabra sin espacios; se distinguen mayúsculas y minúsculas tal como las escribes en el INI.
- Dentro de cada sección hay **pares clave = valor**. Las claves que no se listan en esta referencia como reconocidas se **ignoran** al cargar, salvo las que terminan en `.choices` o `.path` (véase más abajo).

Si el fichero no tiene ninguna sección, la carga falla. En cada sección hace falta **`template`** salvo que `mode` sea **`exec`**, donde se usan `executable` y `arguments` en su lugar.

---

## Claves por comando (sección)

### `template` (obligatorio salvo `mode = exec`)

Texto de la **plantilla** que se ejecuta o abre (modos `shell`, `browser`, `open`). En modo **`exec`** no se usa; define en su lugar `executable` y opcionalmente `arguments`.

Puede incluir **marcadores** `{nombre_param}` que se sustituyen por los valores que el usuario pasa en la línea de órdenes.

**Ejemplo:**

```ini
template = echo Desplegando entorno={env} version={version}
```

- Cada `{clave}` debe coincidir con un **nombre de parámetro** declarado para ese comando (véase `params`, `required`, `*.choices`, `*.path`).
- No uses llaves anidadas ni sintaxis extra: solo `{nombre}` simple.

---

### `description` (opcional)

Texto libre. Se muestra en `mini-launcher --list` junto al nombre del comando.

```ini
description = Despliega una versión en un entorno
```

Si se omite, el comando aparece en la lista sin descripción adicional.

---

### `mode` (opcional)

Define **cómo** se usa la plantilla tras sustituir los marcadores. Valores permitidos (minúsculas o mayúsculas, se normalizan a minúsculas):

| Valor | Comportamiento |
|--------|------------------|
| `shell` | **Por defecto** si omites `mode`. La cadena resultante se pasa al **intérprete de órdenes del sistema** (`subprocess` con `shell=True`). Los valores se escapan para uso en shell con `shlex.quote` (comillas seguras). |
| `browser` | Se interpreta la cadena resultante como **URL** (p. ej. tras sustituir `{termino}` en una query). Los valores se codifican para URL con `urllib.parse.quote_plus` (adecuado para parámetros de búsqueda). Se abre con el **navegador por defecto** (`webbrowser.open`). |
| `open` | La cadena resultante se trata como **ruta de fichero, carpeta o URL** según el sistema. Los valores se insertan **sin** comillas de shell. Antes de abrir se aplica `os.path.normpath`, `os.path.expanduser` y `os.path.expandvars`. En Windows: `os.startfile`; en macOS: `open`; en Linux: `xdg-open`. |
| `exec` | Lanza un **proceso** sin pasar por el shell del sistema (`subprocess` con lista de argumentos, `shell=False`). Requiere **`executable`**; opcionalmente **`arguments`** con marcadores `{param}`. El ejecutable puede ser una ruta absoluta o un nombre resoluble por el **PATH** de Windows (válido también si invocas el launcher desde Git Bash: el proceso hijo es nativo de Windows). Los argumentos se trocean con `shlex.split` (en Windows con reglas adecuadas para rutas con `\`). |

Si pones un `mode` distinto de estos cuatro, la carga del INI **falla**.

---

### `executable` (obligatorio si `mode = exec`)

Ruta al **ejecutable** o nombre del programa (p. ej. `git`, `C:\Program Files\...\app.exe`). Puede contener marcadores `{param}` si el propio camino depende de parámetros.

Tras sustituir placeholders se aplican `os.path.expanduser`, `os.path.expandvars` y `os.path.normpath`.

---

### `arguments` (opcional, solo con `mode = exec`)

Cadena con **argumentos del proceso**, separados como en una línea de órdenes: puede incluir `{param}` que se sustituyen por los valores del usuario **sin** añadir comillas automáticas; puedes poner comillas en el INI si las necesitas.

Ejemplo: `arguments = log -n {n} --oneline`

Tras la sustitución, la cadena se divide con `shlex.split` en la lista de argumentos pasada al ejecutable (el primer elemento del proceso es siempre `executable`; no uses `arguments` para repetir el nombre del exe).

Si omites `arguments` o queda vacío, se ejecuta solo el ejecutable sin argumentos extra.

---

### `params` (opcional en sintaxis, prácticamente necesario)

Lista separada por **comas** de los **nombres de parámetros** que el comando acepta. Los espacios alrededor de cada nombre se recortan.

```ini
params = env, version, nivel
```

**Reglas:**

- Los nombres deben ser identificadores válidos para la CLI: en la terminal se usan como **`--nombre`** (p. ej. `env` → `--env`).
- La unión de `params`, `required`, cualquier `algo.choices` y cualquier `algo.path` determina el conjunto completo de parámetros conocidos para ese comando. Puedes declarar un parámetro solo en `required` o solo en `nombre.choices` sin listarlo en `params`; igualmente se reconoce.

---

### `required` (opcional)

Subconjunto de parámetros **obligatorios**, también como lista separada por comas:

```ini
required = env, version
```

Si falta alguno de estos parámetros en la línea de órdenes, el comando no se ejecuta y se muestra un error.

---

### `nombre.choices` (opcional, repetible por parámetro)

Para el parámetro `nombre`, lista de **valores permitidos** separados por comas. Si el usuario pasa otro valor, el comando se rechaza con error.

```ini
env.choices = dev, staging, prod
```

**Efectos:**

1. **Validación:** el valor debe coincidir exactamente (como texto) con uno de los listados.
2. **Autocompletado** (Bash, PowerShell, shell interactiva): se sugieren esos valores al completar `--env=` o el token de valor.

**Limitación:** los valores no pueden contener una **coma** (el separador es fijo). Si lo necesitas, habría que extender el código.

---

### `nombre.path` (opcional, repetible por parámetro)

Indica si el parámetro `nombre` representa una **ruta de fichero o carpeta** a efectos de **autocompletado en la shell interactiva** (modo `mini-launcher` sin argumentos, con `prompt_toolkit`).

```ini
ruta.path = true
```

Valores que el programa interpreta como verdadero: `1`, `true`, `yes`, `on` (sin distinguir mayúsculas). Cualquier otro valor se trata como falso.

**Efecto:** al completar el valor de ese parámetro, se usa el completado de **rutas del sistema de ficheros** (`PathCompleter`). No afecta a la validación del valor ni al modo `open` por sí solo; solo mejora el Tab en la shell integrada.

---

## Plantilla: sustitución y modos

Para cada parámetro presente en `values`, se reemplaza `{clave}` en `template` (modos distintos de `exec`):

| `mode` | Sustitución del valor en la plantilla |
|--------|----------------------------------------|
| `shell` | `shlex.quote(valor)` — seguro para pasarlo al shell. |
| `browser` | `quote_plus(valor)` — adecuado para componentes de URL (p. ej. términos de búsqueda con espacios). |
| `open` | Valor tal cual (sin comillas automáticas); luego la ruta final se normaliza y expande como se describió arriba. |

En **`exec`**, la sustitución en `executable` y `arguments` es **literal** (valor tal cual, como en `open`), y no se usa `template`.

Si la plantilla contiene un `{clave}` para el que no hay valor, ese marcador **no** se sustituye (no hay error explícito por marcadores sobrantes; conviene que todos los `{...}` tengan parámetro asociado).

---

## Uso en la línea de órdenes (fuera del INI)

Los parámetros se pasan con **opciones largas estilo GNU**:

```text
--parametro valor
--parametro=valor
```

- Con espacios en el valor, usa comillas según tu terminal: `--termino "texto con espacios"`.
- No se admiten parámetros posicionales sueltos: todo debe ir como `--nombre ...`.
- Los nombres en el INI (`env`, `version`) se mapean a `--env` y `--version`.

Restricciones del parser:

- Un token que no sea `--algo` se considera **inválido** (salvo el nombre del comando).
- `--solo` sin valor en la siguiente posición, si el siguiente token es otro `--`, se marca como error (falta valor).

---

## Autocompletado (resumen)

El mismo INI alimenta el modo `--complete` usado por Bash y PowerShell:

- Nombres de **comandos** (secciones).
- Para cada comando: `--param` y, si hay `choices`, valores tras `=`.

Los parámetros con `path = true` solo añaden completado de rutas en la **shell interactiva** integrada, no en el script de Bash/PowerShell (allí no hay `PathCompleter`).

---

## Ejemplo mínimo completo

```ini
[ejemplo]
description = Comando de ejemplo
mode = shell
template = echo Hola {nombre} desde {lugar}
params = nombre, lugar
required = nombre
lugar.choices = aqui, alla
```

Uso:

```text
mini-launcher ejemplo --nombre Ada --lugar aqui
```

## Ejemplo modo `exec`

```ini
[git_log]
description = Ultimas confirmaciones (oneline)
mode = exec
executable = git
arguments = log -n {n} --oneline
params = n
required = n
n.choices = 1, 3, 5
```

```text
mini-launcher git_log --n 5
```

---

## Comentarios y formato INI

El fichero sigue las reglas habituales de `configparser` en Python:

- Líneas que empiezan por `#` o `;` suelen tratarse como comentarios (según versión y contexto).
- Las claves son sensibles a mayúsculas/minúsculas (`optionxform` desactivado en el código).

Evita caracteres ambiguos en los **valores** de listas separadas por comas si esas listas se trocean por comas (`params`, `required`, `*.choices`).

---

## Resumen rápido de claves

| Clave | Obligatoria | Descripción breve |
|-------|-------------|-------------------|
| `template` | Sí, salvo `exec` | Plantilla con `{param}` (`shell` / `browser` / `open`). |
| `description` | No | Texto para `--list`. |
| `mode` | No (`shell` por defecto) | `shell` \| `browser` \| `open` \| `exec`. |
| `executable` | Sí si `exec` | Ejecutable o comando en PATH. |
| `arguments` | No | Argumentos del proceso con `{param}` (solo `exec`). |
| `params` | No* | Lista de parámetros separada por comas. |
| `required` | No | Subconjunto obligatorio separado por comas. |
| `param.choices` | No | Valores permitidos para `param`. |
| `param.path` | No | `true`/`yes`/… para Tab de rutas en shell interactiva. |

\* En la práctica casi siempre definirás al menos `params` o parámetros vía `required` / `*.choices` / `*.path`.
