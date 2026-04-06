# Referencia del fichero de configuración (`commands.ini`)

miniLauncher2 lee un único fichero **INI** (por defecto `commands.ini` en el mismo directorio que `launcher.py`). Puedes usar otro con:

```text
mini-launcher --config C:\ruta\mi_config.ini ...
```

Codificación recomendada: **UTF-8**.

---

## Estructura general

- Cada **sección** `[nombre]` define normalmente **un comando lógico**. El `nombre` es el que escribes en la terminal (`deploy`, `logs`, etc.). Debe ser una sola palabra sin espacios; se distinguen mayúsculas y minúsculas tal como las escribes en el INI.
- La sección reservada **`[mini-launcher]`** no define un comando: solo aporta **valores por defecto globales** (véase más abajo). No aparece en `mini-launcher --list`.
- Dentro de cada sección de comando hay **pares clave = valor**. Las claves que no se listan en esta referencia como reconocidas se **ignoran** al cargar, salvo las que terminan en `.choices` o `.path` (véase más abajo).

Si el fichero no tiene ninguna sección, la carga falla. Debe existir **al menos un comando** (una sección distinta de `[mini-launcher]`).

En cada sección de comando hace falta **`template`** salvo que `mode` sea **`exec`**, donde se usan `executable` y opcionalmente `arguments` en su lugar.

---

## Sección `[mini-launcher]` (opcional)

Configuración **global** que no corresponde a ningún comando. Actualmente solo define el navegador por defecto para los comandos con `mode = browser`.

| Clave | Obligatoria | Descripción |
|--------|-------------|-------------|
| `browser_executable` | No | Ruta o nombre en `PATH` del navegador a usar cuando un comando `browser` no define su propio `executable` y quieres forzar un navegador concreto. Si está **vacío**, los comandos `browser` usan el navegador predeterminado del sistema (`webbrowser.open`). |
| `browser_arguments` | No | Línea de argumentos para ese navegador. Usa el marcador **`{url}`** para la URL final (ya construida a partir del `template` y los parámetros). Si está vacío y sí hay `browser_executable` (global o en el comando), se invoca `[ejecutable, url]` sin argumentos intermedios. |

**Prioridad** respecto a un comando `mode = browser`:

- **Ejecutable:** valor del comando `executable`, o si falta, `browser_executable` de `[mini-launcher]`.
- **Argumentos:** valor del comando `arguments`, o si falta, `browser_arguments` de `[mini-launcher]`.

En `executable` y `arguments` del navegador puedes usar **`{nombre}`** de los parámetros del comando además de **`{url}`** en `arguments`.

Si hay un ejecutable explícito, el proceso se lanza **en segundo plano** (sin bloquear el launcher), con la misma lógica que `exec` con `detach = true`.

**Ejemplo:**

```ini
[mini-launcher]
browser_executable = C:\Program Files\Mozilla Firefox\firefox.exe
browser_arguments = {url}
```

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
| `browser` | Se interpreta la cadena resultante como **URL** (p. ej. tras sustituir `{termino}` en una query). Los valores de parámetros en el `template` se codifican con `urllib.parse.quote_plus` (adecuado para términos de búsqueda). **Sin** `executable` (ni en el comando ni en `[mini-launcher]`): se abre con el **navegador predeterminado** (`webbrowser.open`). **Con** ejecutable configurado: se lanza ese programa con la URL (véase `executable` / `arguments` y `{url}`). |
| `open` | La cadena resultante se trata como **ruta de fichero, carpeta o URL** según el sistema. Los valores se insertan **sin** comillas de shell. Antes de abrir se aplica `os.path.normpath`, `os.path.expanduser` y `os.path.expandvars`. En Windows: `os.startfile`; en macOS: `open`; en Linux: `xdg-open`. |
| `exec` | Lanza un **proceso** sin pasar por el shell del sistema (`subprocess` con lista de argumentos, `shell=False`). Requiere **`executable`**; opcionalmente **`arguments`** con marcadores `{param}`. Opcionalmente **`detach`** para no esperar al proceso. El ejecutable puede ser una ruta absoluta o un nombre resoluble por el **PATH** de Windows (válido también si invocas el launcher desde Git Bash: el proceso hijo es nativo de Windows). Los argumentos se trocean con `shlex.split` (en Windows con reglas adecuadas para rutas con `\`); véase comillas más abajo. |

Si pones un `mode` distinto de estos cuatro, la carga del INI **falla**.

---

### `executable`

- **`mode = exec` (obligatorio):** ruta al **ejecutable** o nombre del programa (p. ej. `git`, `C:\Program Files\...\app.exe`). Puede contener marcadores `{param}` si el propio camino depende de parámetros. Tras sustituir placeholders se aplican `os.path.expanduser`, `os.path.expandvars` y `os.path.normpath`.

- **`mode = browser` (opcional):** si lo defines (o viene de `browser_executable` en `[mini-launcher]`), esa aplicación recibe la URL en lugar de usar `webbrowser`. Si lo omites en el comando y en `[mini-launcher]`, se usa el navegador del sistema.

---

### `arguments`

- **`mode = exec` (opcional):** cadena con **argumentos del proceso**, separados como en una línea de órdenes: puede incluir `{param}` sustituidos por los valores del usuario **sin** añadir comillas automáticas; puedes poner comillas en el INI si las necesitas (p. ej. `":e {fichero}"` para Neovim).

  Tras la sustitución, la cadena se divide con `shlex.split` y, en Windows, se quita **una capa de comillas** que envuelva un argumento entero (para que `-c` reciba el texto sin comillas literales).

  Si omites `arguments` o queda vacío, se ejecuta solo el ejecutable sin argumentos extra.

- **`mode = browser` (opcional):** solo tiene efecto si hay un **`executable`** efectivo (en el comando o por defecto global). Usa **`{url}`** para insertar la URL ya resuelta. También puedes usar **`{param}`** de los parámetros del comando. Se aplica la misma división con `shlex.split` y el mismo tratamiento de comillas externas que en `exec`. Si queda vacío, el argv es `[ejecutable, url]`.

---

### `detach` (opcional, solo `mode = exec`)

Si vale `1`, `true`, `yes` u `on` (sin distinguir mayúsculas), el proceso hijo se **arranca y no se espera** a que termine: el launcher vuelve al instante con código de salida `0` si el arranque fue correcto (el código de salida del hijo no se refleja). Los descriptores estándar del hijo van a `os.devnull`; en Windows se usan banderas de proceso desvinculadas de la consola; en Unix, `start_new_session=True`. Un hilo en segundo plano hace `wait()` sobre el hijo para evitar procesos zombi y fugas de handles.

Si omites `detach` o es falso, **`exec` espera** al proceso y devuelve su código de salida.

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

En **`browser`** con navegador explícito, la URL final obtenida del `template` (tras `apply_template`) se expone como **`{url}`** en `arguments` (y en `executable` solo sustituyen los `{param}` habituales).

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

- Nombres de **comandos** (secciones distintas de `[mini-launcher]`).
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

---

## Ejemplo modo `exec` (esperar al proceso)

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

## Ejemplo modo `exec` (segundo plano)

```ini
[editor]
mode = exec
executable = neovide
arguments = -- -c ":e {fichero}"
detach = true
params = fichero
required = fichero
fichero.path = true
```

---

## Ejemplo modo `browser` con navegador concreto

```ini
[mini-launcher]
browser_executable = C:\Program Files\Google\Chrome\Application\chrome.exe
browser_arguments = {url}

[buscar]
description = Busqueda en Google
mode = browser
template = https://www.google.com/search?q={termino}
params = termino
required = termino
```

O solo en un comando (sin `[mini-launcher]`):

```ini
[buscar]
mode = browser
template = https://example.com/?q={termino}
executable = C:\Program Files\Mozilla Firefox\firefox.exe
arguments = {url}
params = termino
required = termino
```

---

## Comentarios y formato INI

El fichero sigue las reglas habituales de `configparser` en Python:

- Líneas que empiezan por `#` o `;` suelen tratarse como comentarios (según versión y contexto).
- Las claves son sensibles a mayúsculas/minúsculas (`optionxform` desactivado en el código).

Evita caracteres ambiguos en los **valores** de listas separadas por comas si esas listas se trocean por comas (`params`, `required`, `*.choices`).

---

## Resumen rápido de claves

### Sección `[mini-launcher]`

| Clave | Obligatoria | Descripción breve |
|-------|-------------|-------------------|
| `browser_executable` | No | Navegador por defecto para `mode = browser` (vacío = sistema). |
| `browser_arguments` | No | Argumentos con `{url}`; vacío = `[exe, url]`. |

### Sección de cada comando

| Clave | Obligatoria | Descripción breve |
|-------|-------------|-------------------|
| `template` | Sí, salvo `exec` | Plantilla con `{param}` (`shell` / `browser` / `open`). |
| `description` | No | Texto para `--list`. |
| `mode` | No (`shell` por defecto) | `shell` \| `browser` \| `open` \| `exec`. |
| `executable` | Sí si `exec`; opcional si `browser` | Proceso a lanzar; en `browser` sustituye al navegador del sistema si está definido (o el de `[mini-launcher]`). |
| `arguments` | No | `exec`: argumentos con `{param}`. `browser`: con `{url}` y opcionalmente `{param}`. |
| `detach` | No | Solo `exec`: `true`/`yes`/… = no esperar al proceso. |
| `params` | No* | Lista de parámetros separada por comas. |
| `required` | No | Subconjunto obligatorio separado por comas. |
| `param.choices` | No | Valores permitidos para `param`. |
| `param.path` | No | `true`/`yes`/… para Tab de rutas en shell interactiva. |

\* En la práctica casi siempre definirás al menos `params` o parámetros vía `required` / `*.choices` / `*.path`.
