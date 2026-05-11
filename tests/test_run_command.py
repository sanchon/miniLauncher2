"""Pruebas de run_command para los cuatro modos: shell, browser, open, exec."""
import os
import sys
from unittest.mock import call, patch, MagicMock

import pytest

from launcher import run_command


# ---------------------------------------------------------------------------
# Modo shell
# ---------------------------------------------------------------------------

class TestShellMode:

    def test_invoca_subprocess_con_shell_true(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_command(cfg, "deploy", ["--env", "dev", "--version", "1.0"])
            _, kwargs = mock_run.call_args
            assert kwargs["shell"] is True

    def test_template_renderizado_contiene_los_valores(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_command(cfg, "deploy", ["--env", "staging", "--version", "2.5"])
            cmd = mock_run.call_args[0][0]
            assert "staging" in cmd
            assert "2.5" in cmd

    def test_valores_con_espacios_se_escapan_para_shell(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_command(cfg, "deploy", ["--env", "dev", "--version", "1 0"])
            cmd = mock_run.call_args[0][0]
            # shlex.quote envuelve en comillas simples los valores con espacio
            assert "'1 0'" in cmd

    def test_parametros_posicionales_funcionan(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            rc = run_command(cfg, "deploy", ["dev", "1.0"])
            assert rc == 0

    def test_devuelve_el_exit_code_del_proceso(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 42
            rc = run_command(cfg, "deploy", ["--env", "dev", "--version", "1.0"])
            assert rc == 42

    def test_falla_sin_parametro_requerido(self, cfg):
        rc = run_command(cfg, "deploy", [])
        assert rc == 2

    def test_falla_con_un_parametro_requerido_ausente(self, cfg):
        rc = run_command(cfg, "deploy", ["--env", "dev"])
        assert rc == 2

    def test_falla_con_valor_fuera_de_choices(self, cfg):
        rc = run_command(cfg, "deploy", ["--env", "produccion", "--version", "1.0"])
        assert rc == 2

    def test_falla_con_demasiados_positionales(self, cfg):
        # deploy tiene 2 params; pasar 3 posicionales debe fallar
        rc = run_command(cfg, "deploy", ["dev", "1.0", "extra"])
        assert rc == 2


# ---------------------------------------------------------------------------
# Modo browser
# ---------------------------------------------------------------------------

class TestBrowserMode:

    def test_sin_ejecutable_llama_a_webbrowser_open(self, cfg):
        with patch("launcher.webbrowser.open", return_value=True) as mock_open:
            run_command(cfg, "buscar", ["--termino", "python"])
            mock_open.assert_called_once()

    def test_url_contiene_el_termino(self, cfg):
        with patch("launcher.webbrowser.open", return_value=True) as mock_open:
            run_command(cfg, "buscar", ["--termino", "pytest"])
            url = mock_open.call_args[0][0]
            assert "pytest" in url

    def test_terminos_con_espacios_se_codifican_en_la_url(self, cfg):
        with patch("launcher.webbrowser.open", return_value=True) as mock_open:
            run_command(cfg, "buscar", ["--termino", "python asyncio"])
            url = mock_open.call_args[0][0]
            # quote_plus convierte los espacios en '+'
            assert "python+asyncio" in url

    def test_parametro_posicional_funciona(self, cfg):
        with patch("launcher.webbrowser.open", return_value=True) as mock_open:
            rc = run_command(cfg, "buscar", ["pytest"])
            assert rc == 0

    def test_falla_sin_parametro_requerido(self, cfg):
        rc = run_command(cfg, "buscar", [])
        assert rc == 2

    def test_con_ejecutable_usa_proceso_detached(self, cfg):
        with patch("launcher.run_exec_detached", return_value=0) as mock_detach:
            run_command(cfg, "buscar_chrome", ["--q", "python"])
            mock_detach.assert_called_once()

    def test_con_ejecutable_la_url_llega_al_proceso(self, cfg):
        with patch("launcher.run_exec_detached", return_value=0) as mock_detach:
            run_command(cfg, "buscar_chrome", ["--q", "pytest"])
            argv = mock_detach.call_args[0][0]
            assert any("pytest" in str(a) for a in argv)


# ---------------------------------------------------------------------------
# Modo open
# ---------------------------------------------------------------------------

class TestOpenMode:

    def test_llama_a_xdg_open_en_linux(self, cfg):
        with patch("launcher.subprocess.run") as mock_run, \
             patch.object(os, "name", "posix"), \
             patch.object(sys, "platform", "linux"):
            mock_run.return_value.returncode = 0
            run_command(cfg, "abrir", ["--ruta", "/tmp"])
            argv = mock_run.call_args[0][0]
            assert argv[0] == "xdg-open"

    def test_llama_a_open_en_macos(self, cfg):
        with patch("launcher.subprocess.run") as mock_run, \
             patch.object(os, "name", "posix"), \
             patch.object(sys, "platform", "darwin"):
            mock_run.return_value.returncode = 0
            run_command(cfg, "abrir", ["--ruta", "/tmp"])
            argv = mock_run.call_args[0][0]
            assert argv[0] == "open"

    def test_la_ruta_llega_al_comando(self, cfg):
        with patch("launcher.subprocess.run") as mock_run, \
             patch.object(os, "name", "posix"), \
             patch.object(sys, "platform", "linux"):
            mock_run.return_value.returncode = 0
            run_command(cfg, "abrir", ["--ruta", "/tmp"])
            argv = mock_run.call_args[0][0]
            assert "/tmp" in argv[1]

    def test_expande_tilde_en_la_ruta(self, cfg):
        with patch("launcher.subprocess.run") as mock_run, \
             patch.object(os, "name", "posix"), \
             patch.object(sys, "platform", "linux"):
            mock_run.return_value.returncode = 0
            run_command(cfg, "abrir", ["--ruta", "~"])
            argv = mock_run.call_args[0][0]
            assert "~" not in argv[1]
            assert os.path.expanduser("~") in argv[1]

    def test_falla_sin_parametro_requerido(self, cfg):
        rc = run_command(cfg, "abrir", [])
        assert rc == 2


# ---------------------------------------------------------------------------
# Modo exec (bloqueante)
# ---------------------------------------------------------------------------

class TestExecMode:

    def test_invoca_subprocess_sin_shell(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_command(cfg, "git_log", ["--n", "3"])
            _, kwargs = mock_run.call_args
            assert kwargs.get("shell") is False

    def test_argv_contiene_el_ejecutable_y_los_argumentos(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            run_command(cfg, "git_log", ["--n", "5"])
            argv = mock_run.call_args[0][0]
            assert argv[0].endswith("git")
            assert "5" in argv

    def test_parametro_posicional_funciona(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            rc = run_command(cfg, "git_log", ["1"])
            assert rc == 0

    def test_devuelve_el_exit_code_del_proceso(self, cfg):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 128
            rc = run_command(cfg, "git_log", ["--n", "1"])
            assert rc == 128

    def test_falla_sin_parametro_requerido(self, cfg):
        rc = run_command(cfg, "git_log", [])
        assert rc == 2

    def test_falla_con_valor_fuera_de_choices(self, cfg):
        rc = run_command(cfg, "git_log", ["--n", "99"])
        assert rc == 2


# ---------------------------------------------------------------------------
# Modo exec con detach
# ---------------------------------------------------------------------------

class TestExecDetachMode:

    def test_usa_run_exec_detached_en_lugar_de_subprocess(self, cfg):
        with patch("launcher.run_exec_detached", return_value=0) as mock_detach, \
             patch("launcher.subprocess.run") as mock_run:
            run_command(cfg, "editor", ["--fichero", "/tmp/foo.txt"])
            mock_detach.assert_called_once()
            mock_run.assert_not_called()

    def test_el_fichero_llega_al_proceso(self, cfg):
        with patch("launcher.run_exec_detached", return_value=0) as mock_detach:
            run_command(cfg, "editor", ["--fichero", "/tmp/foo.txt"])
            argv = mock_detach.call_args[0][0]
            assert any("foo.txt" in str(a) for a in argv)

    def test_devuelve_0_si_el_arranque_tiene_exito(self, cfg):
        with patch("launcher.run_exec_detached", return_value=0):
            rc = run_command(cfg, "editor", ["--fichero", "/tmp/foo.txt"])
            assert rc == 0

    def test_falla_sin_parametro_requerido(self, cfg):
        rc = run_command(cfg, "editor", [])
        assert rc == 2


# ---------------------------------------------------------------------------
# Comando desconocido
# ---------------------------------------------------------------------------

class TestComandoDesconocido:

    def test_devuelve_2(self, cfg):
        rc = run_command(cfg, "no_existe", [])
        assert rc == 2

    def test_devuelve_2_con_argumentos(self, cfg):
        rc = run_command(cfg, "no_existe", ["--env", "dev"])
        assert rc == 2
