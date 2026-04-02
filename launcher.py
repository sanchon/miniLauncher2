#!/usr/bin/env python3
import configparser
import os
import shlex
import subprocess
import sys
import webbrowser
from pathlib import Path

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory


DEFAULT_CONFIG = Path(__file__).with_name("commands.ini")
DEFAULT_HISTORY = Path(__file__).with_name(".launcher_history")
ALLOWED_MODES = {"shell", "open", "browser"}

BASHRC_BLOCK_START = "# <<< miniLauncher2 bash completion >>>"
BASHRC_BLOCK_END = "# <<< end miniLauncher2 bash completion >>>"


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
    venv_activate = project_dir / ".venv" / "Scripts" / "activate"
    lp = path_for_bash(launcher_py)
    cb = path_for_bash(completion_bash)
    va = path_for_bash(venv_activate)
    lines = [
        BASHRC_BLOCK_START,
        f'if [ -f "{va}" ]; then',
        f'  source "{va}"',
        "fi",
        f"alias launcher='python \"{lp}\"'",
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


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"No existe el archivo de configuración: {config_path}")
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(config_path, encoding="utf-8")

    if not parser.sections():
        raise ValueError("La configuración INI debe tener al menos una sección de comando.")

    commands: dict[str, dict] = {}
    for cmd_name in parser.sections():
        sec = parser[cmd_name]
        template = sec.get("template", "").strip()
        if not template:
            raise ValueError(f"La sección '{cmd_name}' debe definir 'template'.")

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
        for key, raw_val in sec.items():
            if not key.endswith(".choices"):
                continue
            param_name = key[: -len(".choices")].strip()
            values = [x.strip() for x in raw_val.split(",") if x.strip()]
            choices_map[param_name] = values

        all_params = set(params_list) | required | set(choices_map.keys())
        params: dict[str, dict] = {}
        for p in sorted(all_params):
            params[p] = {
                "required": p in required,
                "choices": choices_map.get(p, []),
            }

        description = sec.get("description", "").strip()
        mode = sec.get("mode", "shell").strip().lower()
        if mode not in ALLOWED_MODES:
            raise ValueError(
                f"La sección '{cmd_name}' tiene mode inválido '{mode}'. "
                f"Usa uno de: {', '.join(sorted(ALLOWED_MODES))}."
            )
        commands[cmd_name] = {
            "template": template,
            "description": description,
            "mode": mode,
            "params": params,
        }

    return {"commands": commands}


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


def completion_candidates_from_words(cfg: dict, words: list[str], line_ends_with_space: bool) -> tuple[str, list[str]]:
    if not words:
        return "", list_command_names(cfg)

    if len(words) == 1 and not line_ends_with_space:
        current = words[0]
        return current, list_command_names(cfg)

    if len(words) == 1 and line_ends_with_space:
        cmd_name = words[0]
        params = list_param_names(cfg, cmd_name)
        return "", [f"{p}=" for p in params]

    cmd_name = words[0]
    if line_ends_with_space:
        current = ""
    else:
        current = words[-1]

    used_params = set()
    for tok in words[1:]:
        if "=" in tok:
            used_params.add(tok.split("=", 1)[0])

    if "=" in current:
        p_name, _ = current.split("=", 1)
        vals = list_param_values(cfg, cmd_name, p_name)
        return current, [f"{p_name}={v}" for v in vals]

    params = [p for p in list_param_names(cfg, cmd_name) if p not in used_params]
    return current, [f"{p}=" for p in params]


def render_shell_command(template: str, values: dict[str, str]) -> str:
    out = template
    for key, val in values.items():
        out = out.replace("{" + key + "}", shlex.quote(val))
    return out


def run_command(cfg: dict, command_name: str, args: list[str]) -> int:
    cmd_info = cfg["commands"].get(command_name)
    if cmd_info is None:
        print(f"Comando desconocido: {command_name}", file=sys.stderr)
        return 2

    template = cmd_info.get("template")
    if not template:
        print(f"El comando '{command_name}' no tiene 'template'.", file=sys.stderr)
        return 2

    params_def = cmd_info.get("params", {})
    required = [k for k, v in params_def.items() if isinstance(v, dict) and v.get("required", False)]

    values: dict[str, str] = {}
    unknown: list[str] = []
    for tok in args:
        if "=" not in tok:
            unknown.append(tok)
            continue
        key, val = tok.split("=", 1)
        values[key] = val

    if unknown:
        print(f"Argumentos inválidos (usa clave=valor): {' '.join(unknown)}", file=sys.stderr)
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

    rendered = render_shell_command(template, values)
    mode = str(cmd_info.get("mode", "shell")).lower()

    if mode == "shell":
        print(f"Ejecutando (shell): {rendered}")
        proc = subprocess.run(rendered, shell=True)
        return proc.returncode

    if mode == "browser":
        print(f"Abriendo en navegador: {rendered}")
        ok = webbrowser.open(rendered)
        return 0 if ok else 1

    if mode == "open":
        print(f"Abriendo recurso: {rendered}")
        try:
            if os.name == "nt":
                os.startfile(rendered)  # type: ignore[attr-defined]
                return 0
            if sys.platform == "darwin":
                return subprocess.run(["open", rendered], check=False).returncode
            return subprocess.run(["xdg-open", rendered], check=False).returncode
        except OSError as exc:
            print(f"No se pudo abrir '{rendered}': {exc}", file=sys.stderr)
            return 1

    print(f"Modo no soportado: {mode}", file=sys.stderr)
    return 2


def complete_mode(cfg: dict) -> int:
    line = os.environ.get("COMP_LINE", "")
    point = int(os.environ.get("COMP_POINT", str(len(line))))
    line = line[:point]

    words = line.split()
    current, candidates = completion_candidates_from_words(cfg, words[1:], line.endswith(" "))

    for c in candidates:
        if c.startswith(current):
            print(c)
    return 0


class LauncherCompleter(Completer):
    def __init__(self, cfg: dict):
        self.cfg = cfg

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        words = text_before_cursor.split()
        current, candidates = completion_candidates_from_words(
            self.cfg,
            words,
            text_before_cursor.endswith(" "),
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
    click.echo("miniLauncher shell interactiva. Escribe 'help', 'list', 'exit' o 'quit'.")

    while True:
        try:
            if session is not None:
                line = session.prompt("launcher> ").strip()
            else:
                line = input("launcher> ").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("")
            return 0

        if not line:
            continue

        if line in {"exit", "quit"}:
            return 0
        if line in {"help", "?"}:
            click.echo("Uso: <comando> clave=valor ...")
            click.echo("Comandos internos: list, help, exit, quit")
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

        parts = line.split()
        command = parts[0]
        args = parts[1:]
        run_command(cfg, command, args)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
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
    help="Añade al ~/.bashrc el alias y el script de autocompletado (Git Bash)",
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
def main(
    command: str | None,
    params: tuple[str, ...],
    config: str,
    list_commands: bool,
    complete: bool,
    install_bash_completion: bool,
    uninstall_bash_completion: bool,
    bashrc: str,
) -> None:
    """Launcher CLI configurable."""
    if install_bash_completion and uninstall_bash_completion:
        raise click.ClickException("Usa solo una de: --install-bash-completion o --uninstall-bash-completion")

    if install_bash_completion:
        raise SystemExit(install_bashrc(Path(bashrc)))

    if uninstall_bash_completion:
        raise SystemExit(uninstall_bashrc(Path(bashrc)))

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
