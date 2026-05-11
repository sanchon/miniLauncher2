"""Pruebas de listado de comandos disponibles: CLI (--list) e interactivo (list)."""
import pytest
from launcher import main, list_command_names, run_interactive_line

# Comandos definidos en el INI de prueba (conftest.py)
ALL_COMMANDS = ["abrir", "buscar", "deploy", "git_log", "sin_descripcion"]


class TestCliList:
    """Pruebas del flag --list invocado por línea de comandos."""

    def test_exit_code_ok(self, runner, ini_path):
        result = runner.invoke(main, ["--list", "--config", str(ini_path)])
        assert result.exit_code == 0

    def test_muestra_todos_los_comandos(self, runner, ini_path):
        result = runner.invoke(main, ["--list", "--config", str(ini_path)])
        for cmd in ALL_COMMANDS:
            assert cmd in result.output

    def test_muestra_descripcion(self, runner, ini_path):
        result = runner.invoke(main, ["--list", "--config", str(ini_path)])
        assert "Despliega una version en un entorno" in result.output

    def test_comando_sin_descripcion_aparece_sin_dos_puntos(self, runner, ini_path):
        result = runner.invoke(main, ["--list", "--config", str(ini_path)])
        lines = [l for l in result.output.splitlines() if "sin_descripcion" in l]
        assert lines, "sin_descripcion no aparece en la lista"
        # Sin descripción no debe haber ': ' tras el nombre
        assert ":" not in lines[0]

    def test_orden_alfabetico(self, runner, ini_path):
        result = runner.invoke(main, ["--list", "--config", str(ini_path)])
        lines = [l.strip() for l in result.output.splitlines() if l.strip().startswith("- ")]
        names = [l.split(":")[0].lstrip("- ").strip() for l in lines]
        assert names == sorted(names)

    def test_no_muestra_seccion_mini_launcher(self, runner, ini_path):
        result = runner.invoke(main, ["--list", "--config", str(ini_path)])
        assert "mini-launcher" not in result.output

    def test_config_inexistente_falla(self, runner, tmp_path):
        result = runner.invoke(main, ["--list", "--config", str(tmp_path / "no_existe.ini")])
        assert result.exit_code != 0

    def test_config_vacia_falla(self, runner, tmp_path):
        vacio = tmp_path / "vacio.ini"
        vacio.write_text("", encoding="utf-8")
        result = runner.invoke(main, ["--list", "--config", str(vacio)])
        assert result.exit_code != 0


class TestInteractiveList:
    """Pruebas del comando 'list' dentro de la shell interactiva."""

    def test_continua_el_bucle(self, cfg):
        cont, _ = run_interactive_line(cfg, "list")
        assert cont is True

    def test_muestra_todos_los_comandos(self, cfg):
        _, output = run_interactive_line(cfg, "list")
        for cmd in ALL_COMMANDS:
            assert cmd in output

    def test_muestra_descripcion(self, cfg):
        _, output = run_interactive_line(cfg, "list")
        assert "Despliega una version en un entorno" in output

    def test_comando_sin_descripcion_aparece(self, cfg):
        _, output = run_interactive_line(cfg, "list")
        assert "sin_descripcion" in output

    def test_no_muestra_seccion_mini_launcher(self, cfg):
        _, output = run_interactive_line(cfg, "list")
        assert "mini-launcher" not in output

    def test_linea_vacia_devuelve_output_vacio(self, cfg):
        cont, output = run_interactive_line(cfg, "")
        assert cont is True
        assert output == ""

    def test_help_no_lista_los_comandos(self, cfg):
        _, output = run_interactive_line(cfg, "help")
        for cmd in ALL_COMMANDS:
            assert cmd not in output

    def test_quit_detiene_el_bucle(self, cfg):
        for cmd in ("q", "quit", "exit"):
            cont, _ = run_interactive_line(cfg, cmd)
            assert cont is False, f"'{cmd}' debería detener el bucle"


class TestListCommandNames:
    """Pruebas de la función auxiliar list_command_names."""

    def test_devuelve_lista_ordenada_alfabeticamente(self, cfg):
        names = list_command_names(cfg)
        assert names == sorted(names)

    def test_contiene_todos_los_comandos(self, cfg):
        names = list_command_names(cfg)
        for cmd in ALL_COMMANDS:
            assert cmd in names

    def test_no_incluye_seccion_mini_launcher(self, cfg):
        names = list_command_names(cfg)
        assert "mini-launcher" not in names

    def test_devuelve_lista_no_vacia(self, cfg):
        assert len(list_command_names(cfg)) > 0
