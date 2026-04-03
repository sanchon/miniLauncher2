# Grabar una demo real (asciinema u OBS)

Guía breve para añadir al README un **cast** de asciinema o un **GIF** que muestre el autocompletado con Tab.

## Opción A — asciinema (terminal reproducible)

Ideal: texto nítido, fichero pequeño, se puede incrustar en GitHub con un enlace o subir el `.cast`.

1. Instala el cliente: [asciinema.org/docs/install](https://asciinema.org/docs/install) (en Windows suele usarse **WSL**, **Git Bash** con el binario, o el instalador del sitio).
2. Activa el venv del proyecto y entra en `mini-launcher` (shell interactiva) o usa `l` / `mini-launcher` con el completado ya instalado.
3. Graba:

   ```bash
   asciinema rec demo.cast
   ```

4. Prueba la demo (Tab, un par de comandos), escribe `exit` o `q`, y cierra la grabación con **Ctrl+D** o el comando que indique la herramienta.
5. Sube el `.cast` a [asciinema.org](https://asciinema.org) (cuenta gratuita) y pega la URL en el README, **o** guarda `demo.cast` en el repo (es texto; se puede versionar).

### Pasar el cast a GIF (opcional)

En Linux/macOS o WSL suele usarse **agg** (asciinema gif generator):

```bash
agg demo.cast demo.gif
```

Sube `demo.gif` al repo (por ejemplo `docs/demo.gif`) y en el README:

```markdown
![Demo de autocompletado](docs/demo.gif)
```

## Opción B — OBS + recorte (cualquier terminal)

1. Instala [OBS Studio](https://obsproject.com/).
2. Fuente: captura de ventana o de pantalla; encuadra solo la terminal.
3. Graba 15–30 s mostrando Tab en la shell interactiva o en PowerShell/Git Bash.
4. Exporta vídeo (MP4) y súbelo donde quieras, **o** convierte a GIF con [ffmpeg](https://ffmpeg.org/) (o herramientas online) y añade `docs/demo.gif` como arriba.

## Consejos para la demo

- Aumenta un poco el tamaño de fuente de la terminal antes de grabar.
- Muestra al menos: nombre de comando → `--param=` → valor con choices (si aplica).
- Evita datos personales en la ruta de ficheros.
