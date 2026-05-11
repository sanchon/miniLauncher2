"""Pruebas de validación de load_config cuando el INI no contiene comandos."""
import pytest
from pathlib import Path
from launcher import load_config, main


def ini(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "commands.ini"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Fixtures de INIs sin comandos
# ---------------------------------------------------------------------------

@pytest.fixture
def ini_vacio(tmp_path):
    """INI completamente vacío, sin ninguna sección."""
    return ini(tmp_path, "")


@pytest.fixture
def ini_solo_mini_launcher(tmp_path):
    """INI con solo la sección reservada [mini-launcher], sin comandos reales."""
    return ini(tmp_path, "[mini-launcher]\nbrowser_executable =\n")


@pytest.fixture
def ini_solo_comentarios(tmp_path):
    """INI que solo contiene comentarios, sin secciones."""
    return ini(tmp_path, "# esto es un comentario\n; y esto también\n")


# ---------------------------------------------------------------------------
# load_config directo
# ---------------------------------------------------------------------------

class TestLoadConfigSinComandos:

    def test_vacio_lanza_error(self, ini_vacio):
        with pytest.raises(ValueError):
            load_config(ini_vacio)

    def test_solo_mini_launcher_lanza_error(self, ini_solo_mini_launcher):
        with pytest.raises(ValueError):
            load_config(ini_solo_mini_launcher)

    def test_solo_comentarios_lanza_error(self, ini_solo_comentarios):
        with pytest.raises(ValueError):
            load_config(ini_solo_comentarios)

    def test_fichero_inexistente_lanza_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "no_existe.ini")

    def test_mensaje_error_vacio_es_informativo(self, ini_vacio):
        with pytest.raises(ValueError, match="al menos una sección"):
            load_config(ini_vacio)

    def test_mensaje_error_solo_mini_launcher_es_informativo(self, ini_solo_mini_launcher):
        with pytest.raises(ValueError, match="al menos un comando"):
            load_config(ini_solo_mini_launcher)


# ---------------------------------------------------------------------------
# CLI --list con INIs sin comandos
# ---------------------------------------------------------------------------

class TestCliListSinComandos:

    def test_vacio_exit_code_no_cero(self, runner, ini_vacio):
        result = runner.invoke(main, ["--list", "--config", str(ini_vacio)])
        assert result.exit_code != 0

    def test_solo_mini_launcher_exit_code_no_cero(self, runner, ini_solo_mini_launcher):
        result = runner.invoke(main, ["--list", "--config", str(ini_solo_mini_launcher)])
        assert result.exit_code != 0

    def test_solo_comentarios_exit_code_no_cero(self, runner, ini_solo_comentarios):
        result = runner.invoke(main, ["--list", "--config", str(ini_solo_comentarios)])
        assert result.exit_code != 0

    def test_vacio_muestra_mensaje_de_error(self, runner, ini_vacio):
        result = runner.invoke(main, ["--list", "--config", str(ini_vacio)])
        assert result.output  # hay algún mensaje, no silencio total

    def test_solo_mini_launcher_muestra_mensaje_de_error(self, runner, ini_solo_mini_launcher):
        result = runner.invoke(main, ["--list", "--config", str(ini_solo_mini_launcher)])
        assert result.output


# ---------------------------------------------------------------------------
# CLI ejecutar un comando con INIs sin comandos
# ---------------------------------------------------------------------------

class TestCliRunSinComandos:

    def test_vacio_exit_code_no_cero(self, runner, ini_vacio):
        result = runner.invoke(main, ["--config", str(ini_vacio), "deploy"])
        assert result.exit_code != 0

    def test_solo_mini_launcher_exit_code_no_cero(self, runner, ini_solo_mini_launcher):
        result = runner.invoke(main, ["--config", str(ini_solo_mini_launcher), "deploy"])
        assert result.exit_code != 0
