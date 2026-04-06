#!/usr/bin/env python3
import configparser
import os
import shlex
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory


DEFAULT_CONFIG = Path(__file__).with_name("commands.ini")
DEFAULT_HISTORY = Path(__file__).with_name(".launcher_history")
ALLOWED_MODES = {"shell", "open", "browser", "exec"}
RESERVED_CONFIG_SECTIONS = frozenset({"mini-launcher"})


def split_cli_line(line: str) -> list[str]:
    """Parte una línea tipo shell para el modo interactivo y el autocompletado.

    En Windows, ``posix=False`` evita que ``\\`` en rutas (p.ej. ``C:\\Users\\...``)
    se interpreten como escapes POSIX (``\\U``, ``\\t``, etc.), que corrompen la ruta.
    """
    if not line.strip():
        return []
    posix = os.name != "nt"
    try:
        return shlex.split(line, posix=posix)
    except ValueError:
        return line.split()


def strip_outer_shell_quotes(args: list[str]) -> list[str]:
    """Quita una capa de comillas que envuelve un argumento entero.

    En Windows, ``shlex.split(..., posix=False)`` conserva ``"`` y ``'`` dentro
    del token; hace falta para no romper rutas con ``\\``. Si el usuario agrupa
    un argumento con comillas en ``commands.ini`` (p. ej. ``-c ":e {fichero}"``),
    sin esto Neovim recibiría las comillas como parte del comando ``-c``.
    """
    out: list[str] = []
    for a in args:
        if len(a) >= 2 and a[0] == a[-1] and a[0] in "\"'":
            out.append(a[1:-1])
        else:
            out.append(a)
    return out


def run_exec_detached(argv: list[str]) -> int:
    """Arranca ``argv`` sin bloquear; el hilo demonio hace ``wait()`` al terminar el hijo."""
    kwargs: dict = {
        "shell": False,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    try:
        proc = subprocess.Popen(argv, **kwargs)
    except OSError as exc:
        print(f"No se pudo ejecutar el proceso: {exc}", file=sys.stderr)
        return 1
    threading.Thread(target=proc.wait, daemon=True).start()
    return 0


BASHRC_BLOCK_START = "# <<< miniLauncher2 bash completion >>>"
BASHRC_BLOCK_END = "# <<< end miniLauncher2 bash completion >>>"

POWERSHELL_BLOCK_START = "# <<< miniLauncher2 PowerShell completion >>>"
POWERSHELL_BLOCK_END = "# <<< end miniLauncher2 PowerShell completion >>>"


def path_for_bash(path: Path) -> str:
    """Ruta absoluta usable en Git Bash / MSYS (Windows: C:\\foo -> /c/foo)."""
    p = path.resolve()
    if sys.platform == "win32":
        s = str(p)
        if len(s) >= 2 and s[1] == ":":
            drive = s[0].lower()
            rest = s[2:].replace("\\", "/")
            return f"/{drive}{rest}"
    return str(p).replace("\\", "/")


def bashrc_block_content(project_dir: Path) -> str:
    launcher_py = project_dir / "launcher.py"
    completion_bash = project_dir / "launcher-completion.bash"
    scripts_act = project_dir / ".venv" / "Scripts" / "activate"
    bin_act = project_dir / ".venv" / "bin" / "activate"
    if scripts_act.exists():
        venv_activate = scripts_act
    elif bin_act.exists():
        venv_activate = bin_act
    else:
        venv_activate = scripts_act
    lp = path_for_bash(launcher_py)
    cb = path_for_bash(completion_bash)
    va = path_for_bash(venv_activate)
    lines = [
        BASHRC_BLOCK_START,
        f'if [ -f "{va}" ]; then',
        f'  source "{va}"',
        "fi",
        "if command -v mini-launcher >/dev/null 2>&1; then",
        "  alias l='mini-launcher'",
        "else",
        f'  alias l=\'python "{lp}"\'',
        "fi",
        f'if [ -f "{cb}" ]; then',
        f'  source "{cb}"',
        "fi",
        BASHRC_BLOCK_END,
    ]
    return "\n".join(lines) + "\n"


def install_bashrc(bashrc_path: Path) -> int:
    bashrc_path = bashrc_path.expanduser()
    block = bashrc_block_content(Path(__file__).resolve().parent)
    existing = ""
    if bashrc_path.exists():
        existing = bashrc_path.read_text(encoding="utf-8")
    if BASHRC_BLOCK_START in existing:
        click.echo(f"Ya estaba registrado en: {bashrc_path}")
        return 0
    if existing and not existing.endswith("\n"):
        existing += "\n"
    bashrc_path.parent.mkdir(parents=True, exist_ok=True)
    bashrc_path.write_text(existing + block, encoding="utf-8")
    click.echo(f"Autocompletado Bash registrado en: {bashrc_path}")
    click.echo("Ejecuta: source ~/.bashrc   (o abre una nueva terminal Git Bash)")
    return 0


def uninstall_bashrc(bashrc_path: Path) -> int:
    bashrc_path = bashrc_path.expanduser()
    if not bashrc_path.exists():
        click.echo(f"No existe: {bashrc_path}", err=True)
        return 1
    text = bashrc_path.read_text(encoding="utf-8")
    if BASHRC_BLOCK_START not in text:
        click.echo(f"No hay bloque miniLauncher2 en: {bashrc_path}", err=True)
        return 1
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    skip = False
    for line in lines:
        if BASHRC_BLOCK_START in line:
            skip = True
            continue
        if skip and BASHRC_BLOCK_END in line:
            skip = False
            continue
        if not skip:
            out.append(line)
    bashrc_path.write_text("".join(out), encoding="utf-8")
    click.echo(f"Bloque miniLauncher2 eliminado de: {bashrc_path}")
    return 0


def default_powershell_profile_path() -> Path:
    """Ruta tipica del perfil de PowerShell 6+ (Windows)."""
    return Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"


def ps_single_quoted(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def powershell_profile_block_content(project_dir: Path) -> str:
    project_dir = project_dir.resolve()
    venv_py = project_dir / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        py = str(venv_py)
    else:
        py = sys.executable
    launcher_py = str((project_dir / "launcher.py").resolve())
    py_q = ps_single_quoted(py)
    lp_q = ps_single_quoted(launcher_py)
    lines = [
        POWERSHELL_BLOCK_START,
        f"$MiniLauncherPython = {py_q}",
        f"$MiniLauncherScript = {lp_q}",
        "$MiniLauncherCompletionBlock = {",
        "    param(",
        "        [string]$wordToComplete,",
        "        [System.Management.Automation.Language.Ast]$commandAst,",
        "        [int]$cursorPosition",
        "    )",
        "    $line = $commandAst.Extent.Text",
        "    if ($null -eq $line) { return }",
        "    $env:COMP_LINE = $line",
        "    $env:COMP_POINT = [string]$cursorPosition",
        "    & $MiniLauncherPython $MiniLauncherScript --complete 2>$null | ForEach-Object { $_ }",
        "}.GetNewClosure()",
        "Register-ArgumentCompleter -Native -CommandName 'mini-launcher' -ScriptBlock $MiniLauncherCompletionBlock",
        "Register-ArgumentCompleter -Native -CommandName 'l' -ScriptBlock $MiniLauncherCompletionBlock",
        POWERSHELL_BLOCK_END,
    ]
    return "\n".join(lines) + "\n"


def install_powershell_profile(profile_path: Path) -> int:
    profile_path = profile_path.expanduser()
    block = powershell_profile_block_content(Path(__file__).resolve().parent)
    existing = ""
    if profile_path.exists():
        existing = profile_path.read_text(encoding="utf-8")
    if POWERSHELL_BLOCK_START in existing:
        click.echo(f"Ya estaba registrado en: {profile_path}")
        return 0
    if existing and not existing.endswith("\n"):
        existing += "\n"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(existing + block, encoding="utf-8")
    click.echo(f"Autocompletado PowerShell registrado en: {profile_path}")
    click.echo("Cierra y abre PowerShell o ejecuta: . $PROFILE")
    return 0


def uninstall_powershell_profile(profile_path: Path) -> int:
    profile_path = profile_path.expanduser()
    if not profile_path.exists():
        click.echo(f"No existe: {profile_path}", err=True)
        return 1
    text = profile_path.read_text(encoding="utf-8")
    if POWERSHELL_BLOCK_START not in text:
        click.echo(f"No hay bloque miniLauncher2 en: {profile_path}", err=True)
        return 1
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    skip = False
    for line in lines:
        if POWERSHELL_BLOCK_START in line:
            skip = True
            continue
        if skip and POWERSHELL_BLOCK_END in line:
            skip = False
            continue
        if not skip:
            out.append(line)
    profile_path.write_text("".join(out), encoding="utf-8")
    click.echo(f"Bloque miniLauncher2 eliminado de: {profile_path}")
    return 0


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"No existe el archivo de configuración: {config_path}")
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(config_path, encoding="utf-8")

    if not parser.sections():
        raise ValueError("La configuración INI debe tener al menos una sección de comando.")

    defaults = {"browser_executable": "", "browser_arguments": ""}
    if parser.has_section("mini-launcher"):
        ml = parser["mini-launcher"]
        defaults["browser_executable"] = ml.get("browser_executable", "").strip()
        defaults["browser_arguments"] = ml.get("browser_arguments", "").strip()

    commands: dict[str, dict] = {}
    for cmd_name in parser.sections():
        if cmd_name in RESERVED_CONFIG_SECTIONS:
            continue
        sec = parser[cmd_name]

        required = {
            x.strip()
            for x in sec.get("required", "").split(",")
            if x.strip()
        }
        params_list = [
            x.strip()
            for x in sec.get("params", "").split(",")
            if x.strip()
        ]

        choices_map: dict[str, list[str]] = {}
        path_map: dict[str, bool] = {}
        for key, raw_val in sec.items():
            if key.endswith(".choices"):
                param_name = key[: -len(".choices")].strip()
                values = [x.strip() for x in raw_val.split(",") if x.strip()]
                choices_map[param_name] = values
            elif key.endswith(".path"):
                param_name = key[: -len(".path")].strip()
                path_map[param_name] = raw_val.strip().lower() in ("1", "true", "yes", "on")

        all_params = set(params_list) | required | set(choices_map.keys()) | set(path_map.keys())
        params: dict[str, dict] = {}
        for p in sorted(all_params):
            params[p] = {
                "required": p in required,
                "choices": choices_map.get(p, []),
                "path": path_map.get(p, False),
            }

        description = sec.get("description", "").strip()
        mode = sec.get("mode", "shell").strip().lower()
        if mode not in ALLOWED_MODES:
            raise ValueError(
                f"La sección '{cmd_name}' tiene mode inválido '{mode}'. "
                f"Usa uno de: {', '.join(sorted(ALLOWED_MODES))}."
            )

        template = sec.get("template", "").strip()
        executable_line = sec.get("executable", "").strip()
        arguments_line = sec.get("arguments", "").strip()

        detach_line = sec.get("detach", "").strip().lower()
        detach = detach_line in ("1", "true", "yes", "on")

        if mode == "exec":
            if not executable_line:
                raise ValueError(
                    f"La sección '{cmd_name}' con mode=exec debe definir 'executable' "
                    f"(ruta al ejecutable o nombre resoluble por el sistema, p. ej. git o C:\\\\...\\\\app.exe)."
                )
        elif not template:
            raise ValueError(f"La sección '{cmd_name}' debe definir 'template'.")

        commands[cmd_name] = {
            "template": template,
            "description": description,
            "mode": mode,
            "params": params,
            "executable": executable_line,
            "arguments": arguments_line,
            "detach": detach if mode == "exec" else False,
        }

    if not commands:
        raise ValueError(
            "La configuración INI debe incluir al menos un comando "
            "(una sección distinta de [mini-launcher])."
        )

    return {"commands": commands, "defaults": defaults}


def list_command_names(cfg: dict) -> list[str]:
    return sorted(cfg["commands"].keys())


def list_param_names(cfg: dict, cmd_name: str) -> list[str]:
    cmd = cfg["commands"].get(cmd_name, {})
    params = cmd.get("params", {})
    if not isinstance(params, dict):
        return []
    return sorted(params.keys())


def list_param_values(cfg: dict, cmd_name: str, param_name: str) -> list[str]:
    cmd = cfg["commands"].get(cmd_name, {})
    params = cmd.get("params", {})
    p = params.get(param_name, {})
    choices = p.get("choices", [])
    if not isinstance(choices, list):
        return []
    return [str(x) for x in choices]


def parse_long_options(args: list[str], valid_params: set[str]) -> tuple[dict[str, str], list[str]]:
    """Parsea `--k v`, `--k=v`. Devuelve (valores, tokens no reconocidos / posicionales)."""
    values: dict[str, str] = {}
    unknown: list[str] = []
    i = 0
    while i < len(args):
        tok = args[i]
        if not tok.startswith("--"):
            unknown.append(tok)
            i += 1
            continue
        opt = tok[2:]
        if "=" in opt:
            key, val = opt.split("=", 1)
            if key not in valid_params:
                unknown.append(tok)
            else:
                values[key] = val
            i += 1
            continue
        key = opt
        if key not in valid_params:
            unknown.append(tok)
            i += 1
            continue
        if i + 1 < len(args) and not args[i + 1].startswith("--"):
            values[key] = args[i + 1]
            i += 2
        else:
            unknown.append(tok)
            i += 1
    return values, unknown


def _parse_rest_for_completion(rest: list[str]) -> tuple[dict[str, str], str | None]:
    """used params; pending = nombre de param si falta el valor (--foo al final)."""
    used: dict[str, str] = {}
    pending: str | None = None
    i = 0
    while i < len(rest):
        t = rest[i]
        if not t.startswith("--"):
            i += 1
            continue
        body = t[2:]
        if "=" in body:
            k, v = body.split("=", 1)
            used[k] = v
            pending = None
            i += 1
            continue
        k = body
        if i + 1 < len(rest) and not rest[i + 1].startswith("--"):
            used[k] = rest[i + 1]
            pending = None
            i += 2
        else:
            pending = k
            i += 1
    return used, pending


def completion_candidates_from_words(cfg: dict, words: list[str], line_ends_with_space: bool) -> tuple[str, list[str]]:
    if not words:
        return "", list_command_names(cfg)

    if len(words) == 1 and not line_ends_with_space:
        current = words[0]
        return current, list_command_names(cfg)

    if len(words) == 1 and line_ends_with_space:
        cmd_name = words[0]
        params = list_param_names(cfg, cmd_name)
        return "", [f"--{p}" for p in params]

    cmd_name = words[0]
    param_names = list_param_names(cfg, cmd_name)
    pname_set = set(param_names)

    if line_ends_with_space:
        current = ""
        rest = words[1:]
    else:
        current = words[-1]
        rest = words[1:-1]

    used, pending = _parse_rest_for_completion(rest)

    if line_ends_with_space:
        if pending:
            vals = list_param_values(cfg, cmd_name, pending)
            if vals:
                return "", vals
            return "", []
        unused = [p for p in param_names if p not in used]
        return "", [f"--{p}" for p in unused]

    if current.startswith("--"):
        if "=" in current:
            key, partial = current[2:].split("=", 1)
            if key not in pname_set:
                return current, []
            vals = list_param_values(cfg, cmd_name, key)
            if vals:
                return current, [f"--{key}={v}" for v in vals if str(v).startswith(partial)]
            return current, []
        prefix = current[2:]
        unused = [p for p in param_names if p not in used]
        matches = [f"--{p}" for p in unused if p.startswith(prefix)]
        return current, matches

    if pending:
        vals = list_param_values(cfg, cmd_name, pending)
        if vals:
            return current, [v for v in vals if str(v).startswith(current)]
        return current, []

    return current, []


def path_completion_context(cfg: dict, text_before_cursor: str) -> str | None:
    """Si el cursor completa el valor de un parametro marcado como ruta, devuelve el fragmento de ruta (puede ser '')."""
    if not text_before_cursor.strip():
        return None
    line_ends_space = text_before_cursor[-1].isspace()
    words = split_cli_line(text_before_cursor.rstrip())
    if not words:
        return None
    cmd = words[0]
    if cmd not in cfg.get("commands", {}):
        return None

    params_meta = cfg["commands"][cmd]["params"]

    def is_path(name: str) -> bool:
        p = params_meta.get(name, {})
        return bool(p.get("path"))

    if line_ends_space:
        current = ""
        rest = words[1:]
    else:
        current = words[-1]
        rest = words[1:-1]

    used, pending = _parse_rest_for_completion(rest)

    if line_ends_space and pending and is_path(pending):
        return ""

    if not line_ends_space and pending and is_path(pending):
        if current.startswith("--"):
            return None
        return current

    if not line_ends_space and current.startswith("--") and "=" in current:
        key, partial = current[2:].split("=", 1)
        if key in params_meta and is_path(key):
            return partial

    return None


def substitute_placeholders(template: str, values: dict[str, str]) -> str:
    """Sustituye {clave} por el valor tal cual (sin comillas); para rutas y argumentos de proceso."""
    out = template
    for key, val in values.items():
        out = out.replace("{" + key + "}", val)
    return out


def apply_template(template: str, values: dict[str, str], mode: str) -> str:
    out = template
    for key, val in values.items():
        if mode == "shell":
            repl = shlex.quote(val)
        elif mode == "browser":
            repl = quote_plus(val)
        else:
            repl = val
        out = out.replace("{" + key + "}", repl)
    return out


def run_command(cfg: dict, command_name: str, args: list[str]) -> int:
    cmd_info = cfg["commands"].get(command_name)
    if cmd_info is None:
        print(f"Comando desconocido: {command_name}", file=sys.stderr)
        return 2

    mode = str(cmd_info.get("mode", "shell")).lower()
    template = cmd_info.get("template") or ""

    params_def = cmd_info.get("params", {})
    required = [k for k, v in params_def.items() if isinstance(v, dict) and v.get("required", False)]
    valid_names = set(params_def.keys())

    values, unknown = parse_long_options(args, valid_names)

    if unknown:
        print(
            f"Argumentos inválidos (usa --param valor o --param=valor): {' '.join(unknown)}",
            file=sys.stderr,
        )
        return 2

    missing = [k for k in required if k not in values]
    if missing:
        print(f"Faltan parámetros obligatorios: {', '.join(missing)}", file=sys.stderr)
        return 2

    for p_name, p_def in params_def.items():
        if p_name not in values:
            continue
        choices = p_def.get("choices", [])
        if choices and values[p_name] not in [str(c) for c in choices]:
            print(
                f"Valor inválido para '{p_name}': {values[p_name]}. "
                f"Opciones: {', '.join(str(c) for c in choices)}",
                file=sys.stderr,
            )
            return 2

    if mode == "exec":
        exe_t = cmd_info.get("executable", "").strip()
        arg_t = cmd_info.get("arguments", "").strip()
        exe_rendered = substitute_placeholders(exe_t, values)
        arg_rendered = substitute_placeholders(arg_t, values)
        posix = os.name != "nt"
        try:
            raw_args = shlex.split(arg_rendered, posix=posix) if arg_rendered.strip() else []
            arg_list = strip_outer_shell_quotes(raw_args)
        except ValueError as exc:
            print(f"No se pudo interpretar 'arguments' (revisa comillas): {exc}", file=sys.stderr)
            return 2
        exe_final = os.path.normpath(os.path.expanduser(os.path.expandvars(exe_rendered)))
        argv = [exe_final] + arg_list
        detach = bool(cmd_info.get("detach"))
        tag = "exec, segundo plano" if detach else "exec"
        print(f"Ejecutando ({tag}): {argv}", flush=True)
        try:
            if detach:
                return run_exec_detached(argv)
            proc = subprocess.run(argv, shell=False)
            return proc.returncode
        except OSError as exc:
            print(f"No se pudo ejecutar el proceso: {exc}", file=sys.stderr)
            return 1

    if not template:
        print(f"El comando '{command_name}' no tiene 'template'.", file=sys.stderr)
        return 2

    rendered = apply_template(template, values, mode)

    if mode == "shell":
        print(f"Ejecutando (shell): {rendered}")
        proc = subprocess.run(rendered, shell=True)
        return proc.returncode

    if mode == "browser":
        defs = cfg.get("defaults") or {}
        exe_t = (cmd_info.get("executable") or "").strip() or (defs.get("browser_executable") or "").strip()
        arg_t = (cmd_info.get("arguments") or "").strip() or (defs.get("browser_arguments") or "").strip()
        if not exe_t:
            print(f"Abriendo en navegador (predeterminado del sistema): {rendered}")
            ok = webbrowser.open(rendered)
            return 0 if ok else 1
        exe_rendered = substitute_placeholders(exe_t, values)
        exe_final = os.path.normpath(os.path.expanduser(os.path.expandvars(exe_rendered)))
        merged = dict(values)
        merged["url"] = rendered
        arg_rendered = substitute_placeholders(arg_t, merged) if arg_t else ""
        posix = os.name != "nt"
        if not arg_rendered.strip():
            argv = [exe_final, rendered]
        else:
            try:
                raw_args = shlex.split(arg_rendered, posix=posix)
                arg_list = strip_outer_shell_quotes(raw_args)
            except ValueError as exc:
                print(
                    f"No se pudo interpretar 'arguments' del navegador (revisa comillas y {{url}}): {exc}",
                    file=sys.stderr,
                )
                return 2
            argv = [exe_final] + arg_list
        print(f"Abriendo en navegador: {argv}", flush=True)
        return run_exec_detached(argv)

    if mode == "open":
        path = os.path.normpath(os.path.expanduser(os.path.expandvars(rendered)))
        print(f"Abriendo recurso: {path}")
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
                return 0
            if sys.platform == "darwin":
                return subprocess.run(["open", path], check=False).returncode
            return subprocess.run(["xdg-open", path], check=False).returncode
        except OSError as exc:
            print(f"No se pudo abrir '{path}': {exc}", file=sys.stderr)
            return 1

    print(f"Modo no soportado: {mode}", file=sys.stderr)
    return 2


def complete_mode(cfg: dict) -> int:
    line = os.environ.get("COMP_LINE", "")
    point = int(os.environ.get("COMP_POINT", str(len(line))))
    line = line[:point]

    line_ends_with_space = bool(line) and line[-1].isspace()
    words = split_cli_line(line) if line.strip() else []
    current, candidates = completion_candidates_from_words(cfg, words[1:], line_ends_with_space)

    for c in candidates:
        if c.startswith(current):
            print(c)
    return 0


class LauncherCompleter(Completer):
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self._path_completer = PathCompleter(expanduser=True)

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        frag = path_completion_context(self.cfg, text_before_cursor)
        if frag is not None:
            sub = Document(frag, cursor_position=len(frag))
            yield from self._path_completer.get_completions(sub, complete_event)
            return

        line_ends_with_space = bool(text_before_cursor) and text_before_cursor[-1].isspace()
        words = split_cli_line(text_before_cursor) if text_before_cursor.strip() else []
        current, candidates = completion_candidates_from_words(
            self.cfg,
            words,
            line_ends_with_space,
        )
        for candidate in candidates:
            if candidate.startswith(current):
                yield Completion(candidate, start_position=-len(current))


def run_interactive_shell(cfg: dict) -> int:
    use_prompt_toolkit = sys.stdin.isatty() and sys.stdout.isatty()
    session = None
    if use_prompt_toolkit:
        session = PromptSession(
            completer=LauncherCompleter(cfg),
            history=FileHistory(str(DEFAULT_HISTORY)),
        )
    click.echo("miniLauncher shell interactiva. Escribe 'help', 'list', 'q', 'exit' o 'quit'.")

    while True:
        try:
            if session is not None:
                line = session.prompt("l> ").strip()
            else:
                line = input("l> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("")
            return 0

        if not line:
            continue

        if line in {"exit", "quit", "q"}:
            return 0
        if line in {"help", "?"}:
            click.echo('Uso: <comando> --param valor ...  (también --param="valor con espacios")')
            click.echo("Comandos internos: list, help, q, exit, quit")
            continue
        if line == "list":
            click.echo("Comandos disponibles:")
            for c in list_command_names(cfg):
                desc = cfg["commands"].get(c, {}).get("description", "")
                if desc:
                    click.echo(f" - {c}: {desc}")
                else:
                    click.echo(f" - {c}")
            continue

        parts = split_cli_line(line)
        command = parts[0]
        args = parts[1:]
        run_command(cfg, command, args)


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
        # Las opciones del comando (p.ej. --env) no son opciones de Click
        "ignore_unknown_options": True,
    }
)
@click.argument("command", required=False)
@click.argument("params", nargs=-1)
@click.option(
    "--config",
    default=str(DEFAULT_CONFIG),
    show_default=True,
    help="Ruta al archivo de configuración INI",
)
@click.option("--list", "list_commands", is_flag=True, help="Lista comandos disponibles")
@click.option("--complete", is_flag=True, hidden=True)
@click.option(
    "--install-bash-completion",
    is_flag=True,
    help="Añade al ~/.bashrc el alias l y el script de autocompletado (Git Bash)",
)
@click.option(
    "--uninstall-bash-completion",
    is_flag=True,
    help="Elimina del ~/.bashrc el bloque añadido por --install-bash-completion",
)
@click.option(
    "--bashrc",
    default="~/.bashrc",
    show_default=True,
    help="Fichero bashrc a modificar (por defecto ~/.bashrc)",
)
@click.option(
    "--install-powershell-completion",
    is_flag=True,
    help="Añade al perfil de PowerShell el autocompletado nativo (Tab)",
)
@click.option(
    "--uninstall-powershell-completion",
    is_flag=True,
    help="Elimina del perfil de PowerShell el bloque instalado",
)
@click.option(
    "--powershell-profile",
    type=click.Path(path_type=Path),
    default=None,
    help="Ruta al perfil de PowerShell (por defecto Documents/PowerShell/Microsoft.PowerShell_profile.ps1)",
)
def main(
    command: str | None,
    params: tuple[str, ...],
    config: str,
    list_commands: bool,
    complete: bool,
    install_bash_completion: bool,
    uninstall_bash_completion: bool,
    bashrc: str,
    install_powershell_completion: bool,
    uninstall_powershell_completion: bool,
    powershell_profile: Path | None,
) -> None:
    """Launcher CLI configurable."""
    if install_bash_completion and uninstall_bash_completion:
        raise click.ClickException("Usa solo una de: --install-bash-completion o --uninstall-bash-completion")
    if install_powershell_completion and uninstall_powershell_completion:
        raise click.ClickException(
            "Usa solo una de: --install-powershell-completion o --uninstall-powershell-completion"
        )

    if install_bash_completion:
        code = install_bashrc(Path(bashrc))
        if code != 0:
            raise SystemExit(code)
    if uninstall_bash_completion:
        code = uninstall_bashrc(Path(bashrc))
        if code != 0:
            raise SystemExit(code)

    ps_path = powershell_profile if powershell_profile is not None else default_powershell_profile_path()
    if install_powershell_completion:
        code = install_powershell_profile(ps_path)
        if code != 0:
            raise SystemExit(code)
    if uninstall_powershell_completion:
        code = uninstall_powershell_profile(ps_path)
        if code != 0:
            raise SystemExit(code)

    if (
        install_bash_completion
        or uninstall_bash_completion
        or install_powershell_completion
        or uninstall_powershell_completion
    ):
        return

    try:
        cfg = load_config(Path(config))
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if complete:
        raise SystemExit(complete_mode(cfg))

    if list_commands:
        click.echo("Comandos disponibles:")
        for c in list_command_names(cfg):
            desc = cfg["commands"].get(c, {}).get("description", "")
            if desc:
                click.echo(f" - {c}: {desc}")
            else:
                click.echo(f" - {c}")
        return

    if not command:
        raise SystemExit(run_interactive_shell(cfg))

    raise SystemExit(run_command(cfg, command, list(params)))


if __name__ == "__main__":
    main()
