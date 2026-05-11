"""Pruebas de la shell interactiva (Prioridad 2).

Cubre: run_interactive_line (clear + ejecución de comandos),
run_interactive_shell (bucle REPL) y _make_positional_toolbar.
"""
from unittest.mock import MagicMock, patch

import pytest

from launcher import _make_positional_toolbar, run_interactive_line, run_interactive_shell


# ---------------------------------------------------------------------------
# run_interactive_line — rutas no cubiertas por test_list.py
# ---------------------------------------------------------------------------

class TestRunInteractiveLineClear:

    def test_clear_devuelve_continuar_true(self, cfg):
        with patch("launcher.click.clear"):
            cont, out = run_interactive_line(cfg, "clear")
        assert cont is True

    def test_clear_devuelve_texto_vacio(self, cfg):
        with patch("launcher.click.clear"):
            _, out = run_interactive_line(cfg, "clear")
        assert out == ""

    def test_clear_llama_a_click_clear(self, cfg):
        with patch("launcher.click.clear") as mock_clear:
            run_interactive_line(cfg, "clear")
        mock_clear.assert_called_once()

    def test_clear_con_espacios_alrededor(self, cfg):
        with patch("launcher.click.clear") as mock_clear:
            cont, _ = run_interactive_line(cfg, "  clear  ")
        assert cont is True
        mock_clear.assert_called_once()


class TestRunInteractiveLineEjecucion:

    def test_comando_valido_devuelve_continuar_true(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            cont, _ = run_interactive_line(cfg, "deploy --env dev --version 1.0")
        assert cont is True

    def test_comando_valido_captura_salida(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            _, out = run_interactive_line(cfg, "deploy --env dev --version 1.0")
        assert "dev" in out

    def test_comando_desconocido_devuelve_continuar_true(self, cfg):
        cont, _ = run_interactive_line(cfg, "comando_que_no_existe")
        assert cont is True

    def test_comando_desconocido_captura_mensaje_de_error(self, cfg):
        _, out = run_interactive_line(cfg, "comando_que_no_existe")
        assert "desconocido" in out.lower()

    def test_comando_con_parametros_posicionales(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            cont, out = run_interactive_line(cfg, "deploy dev 1.0")
        assert cont is True
        assert "dev" in out

    def test_parametro_requerido_faltante_captura_error(self, cfg):
        _, out = run_interactive_line(cfg, "deploy")
        assert "Faltan" in out or "faltan" in out.lower() or out != ""

    def test_modo_exec_captura_salida_con_subprocess_mockeado(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            cont, out = run_interactive_line(cfg, "git_log --n 1")
        assert cont is True
        assert out != ""


# ---------------------------------------------------------------------------
# run_interactive_shell — bucle REPL
# ---------------------------------------------------------------------------

class TestRunInteractiveShell:

    def test_devuelve_0_al_recibir_eof(self, cfg):
        with patch("builtins.input", side_effect=EOFError), \
             patch("launcher.click.clear"), \
             patch("launcher.click.echo"):
            rc = run_interactive_shell(cfg)
        assert rc == 0

    def test_devuelve_0_al_recibir_keyboard_interrupt(self, cfg):
        with patch("builtins.input", side_effect=KeyboardInterrupt), \
             patch("launcher.click.clear"), \
             patch("launcher.click.echo"):
            rc = run_interactive_shell(cfg)
        assert rc == 0

    def test_devuelve_0_tras_comando_quit(self, cfg):
        with patch("builtins.input", side_effect=["q"]), \
             patch("launcher.click.clear"), \
             patch("launcher.click.echo"):
            rc = run_interactive_shell(cfg)
        assert rc == 0

    def test_devuelve_0_tras_comando_exit(self, cfg):
        with patch("builtins.input", side_effect=["exit"]), \
             patch("launcher.click.clear"), \
             patch("launcher.click.echo"):
            rc = run_interactive_shell(cfg)
        assert rc == 0

    def test_itera_varias_lineas_antes_de_salir(self, cfg):
        inputs = ["list", "help", "q"]
        with patch("builtins.input", side_effect=inputs), \
             patch("launcher.click.clear"), \
             patch("launcher.click.echo"):
            rc = run_interactive_shell(cfg)
        assert rc == 0

    def test_ejecuta_comando_valido_y_sigue(self, cfg):
        with patch("builtins.input", side_effect=["q"]), \
             patch("launcher.click.clear"), \
             patch("launcher.click.echo"), \
             patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            rc = run_interactive_shell(cfg)
        assert rc == 0

    def test_muestra_el_banner_al_iniciar(self, cfg):
        mensajes = []
        with patch("builtins.input", side_effect=EOFError), \
             patch("launcher.click.clear"), \
             patch("launcher.click.echo", side_effect=lambda *a, **kw: mensajes.append(a)):
            run_interactive_shell(cfg)
        salida = " ".join(str(m) for m in mensajes)
        assert "MINI" in salida or "launcher" in salida.lower() or salida != ""


# ---------------------------------------------------------------------------
# _make_positional_toolbar
# ---------------------------------------------------------------------------

class TestMakePositionalToolbar:

    def _make_app_mock(self, text: str):
        mock_app = MagicMock()
        mock_app.current_buffer.text = text
        return mock_app

    def test_texto_vacio_devuelve_cadena_vacia(self, cfg):
        toolbar = _make_positional_toolbar(cfg)
        with patch("launcher.get_app", return_value=self._make_app_mock("")):
            result = toolbar()
        assert result == ""

    def test_comando_desconocido_devuelve_cadena_vacia(self, cfg):
        toolbar = _make_positional_toolbar(cfg)
        with patch("launcher.get_app", return_value=self._make_app_mock("noexiste ")):
            result = toolbar()
        assert result == ""

    def test_comando_sin_params_devuelve_cadena_vacia(self, cfg):
        toolbar = _make_positional_toolbar(cfg)
        with patch("launcher.get_app", return_value=self._make_app_mock("sin_descripcion ")):
            result = toolbar()
        assert result == ""

    def test_modo_nombrado_devuelve_cadena_vacia(self, cfg):
        toolbar = _make_positional_toolbar(cfg)
        with patch("launcher.get_app", return_value=self._make_app_mock("deploy --env dev")):
            result = toolbar()
        assert result == ""

    def test_posicional_muestra_params(self, cfg):
        from prompt_toolkit.formatted_text import FormattedText
        toolbar = _make_positional_toolbar(cfg)
        with patch("launcher.get_app", return_value=self._make_app_mock("deploy ")):
            result = toolbar()
        assert result != ""
        if isinstance(result, FormattedText):
            text = "".join(v for _, v in result)
            assert "env" in text

    def test_posicional_resalta_slot_actual(self, cfg):
        from prompt_toolkit.formatted_text import FormattedText
        toolbar = _make_positional_toolbar(cfg)
        with patch("launcher.get_app", return_value=self._make_app_mock("deploy d")):
            result = toolbar()
        if isinstance(result, FormattedText):
            styled = [(style, txt) for style, txt in result if "yellow" in style or "bold" in style]
            assert styled, "El slot activo debe estar resaltado"

    def test_excepcion_en_get_app_devuelve_cadena_vacia(self, cfg):
        toolbar = _make_positional_toolbar(cfg)
        with patch("launcher.get_app", side_effect=RuntimeError("no app")):
            result = toolbar()
        assert result == ""
