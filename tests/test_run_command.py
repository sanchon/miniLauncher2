"""Pruebas de run_command para los cuatro modos: shell, browser, open, exec."""
import os
import sys
from unittest.mock import call, patch, MagicMock

import pytest

from launcher import parse_long_options, run_command


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


# ---------------------------------------------------------------------------
# parse_long_options — casos de borde no cubiertos
# ---------------------------------------------------------------------------

class TestParseLongOptions:

    def test_formato_key_igual_val_conocido(self):
        values, unknown = parse_long_options(["--env=dev"], {"env"})
        assert values == {"env": "dev"}
        assert unknown == []

    def test_formato_key_igual_val_clave_desconocida(self):
        values, unknown = parse_long_options(["--otro=val"], {"env"})
        assert values == {}
        assert "--otro=val" in unknown

    def test_clave_desconocida_sin_valor(self):
        values, unknown = parse_long_options(["--otro"], {"env"})
        assert "--otro" in unknown

    def test_flag_conocido_sin_valor_al_final(self):
        values, unknown = parse_long_options(["--env"], {"env"})
        assert "--env" in unknown

    def test_flag_conocido_seguido_de_otro_flag(self):
        values, unknown = parse_long_options(["--env", "--version"], {"env", "version"})
        assert "--env" in unknown

    def test_mezcla_conocidos_e_incognitos(self):
        values, unknown = parse_long_options(
            ["--env", "dev", "--otro"], {"env"}
        )
        assert values == {"env": "dev"}
        assert "--otro" in unknown


# ---------------------------------------------------------------------------
# Rutas de error en run_command no cubiertas
# ---------------------------------------------------------------------------

class TestRunCommandRutasDeError:

    # -- exec: ValueError al parsear arguments
    def test_exec_arguments_malformados_devuelve_2(self, cfg):
        with patch("launcher.shlex.split", side_effect=ValueError("comilla sin cerrar")):
            rc = run_command(cfg, "git_log", ["--n", "1"])
        assert rc == 2

    # -- exec: OSError al lanzar subprocess.run
    def test_exec_oserror_al_ejecutar_devuelve_1(self, cfg):
        with patch("launcher.subprocess.run", side_effect=OSError("no encontrado")):
            rc = run_command(cfg, "git_log", ["--n", "1"])
        assert rc == 1

    # -- browser: webbrowser.open devuelve False
    def test_browser_webbrowser_falla_devuelve_1(self, cfg):
        with patch("launcher.webbrowser.open", return_value=False):
            rc = run_command(cfg, "buscar", ["--termino", "python"])
        assert rc == 1

    # -- browser con ejecutable: ValueError al parsear arguments
    def test_browser_arguments_malformados_devuelve_2(self, cfg):
        with patch("launcher.shlex.split", side_effect=ValueError("comilla sin cerrar")):
            rc = run_command(cfg, "buscar_chrome", ["--q", "python"])
        assert rc == 2

    # -- browser con ejecutable sin arguments: pasa la URL directamente
    def test_browser_con_ejecutable_sin_arguments_usa_url(self, cfg):
        cfg["commands"]["buscar_chrome"]["arguments"] = ""
        with patch("launcher.run_exec_detached", return_value=0) as mock_detach:
            rc = run_command(cfg, "buscar_chrome", ["--q", "python"])
        assert rc == 0
        argv = mock_detach.call_args[0][0]
        assert any("python" in str(a) for a in argv)

    # -- open: OSError al llamar a xdg-open
    def test_open_oserror_devuelve_1(self, cfg):
        with patch("launcher.subprocess.run", side_effect=OSError("xdg-open no encontrado")), \
             patch.object(os, "name", "posix"), \
             patch.object(sys, "platform", "linux"):
            rc = run_command(cfg, "abrir", ["--ruta", "/tmp"])
        assert rc == 1

    # -- open: ruta en Windows llama a os.startfile
    def test_open_windows_llama_a_startfile(self, cfg):
        with patch.object(os, "name", "nt"), \
             patch("os.startfile", create=True) as mock_startfile:
            rc = run_command(cfg, "abrir", ["--ruta", "/tmp"])
        assert rc == 0
        mock_startfile.assert_called_once()

    # -- template vacío en modo no-exec
    def test_sin_template_en_modo_shell_devuelve_2(self, cfg):
        cfg["commands"]["deploy"]["template"] = ""
        rc = run_command(cfg, "deploy", ["--env", "dev", "--version", "1.0"])
        assert rc == 2

    # -- modo no soportado (fallback defensivo)
    def test_modo_no_soportado_devuelve_2(self, cfg):
        cfg["commands"]["deploy"]["mode"] = "modo_inventado"
        rc = run_command(cfg, "deploy", ["--env", "dev", "--version", "1.0"])
        assert rc == 2

    # -- choices: param opcional no proporcionado activa el continue (línea 772)
    def test_param_opcional_no_proporcionado_omite_validacion_de_choices(self, cfg):
        cfg["commands"]["deploy"]["params"]["verbose"] = {
            "required": False,
            "choices": ["true", "false"],
            "path": False,
        }
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            rc = run_command(cfg, "deploy", ["--env", "dev", "--version", "1.0"])
        assert rc == 0


# ---------------------------------------------------------------------------
# load_config — rutas de error no cubiertas
# ---------------------------------------------------------------------------

class TestLoadConfigRutasDeError:

    def _ini(self, tmp_path, content):
        from pathlib import Path
        p = tmp_path / "test.ini"
        p.write_text(content, encoding="utf-8")
        return p

    def test_mode_invalido_lanza_value_error(self, tmp_path):
        from launcher import load_config
        p = self._ini(tmp_path, "[cmd]\nmode = teleport\ntemplate = echo hi\n")
        with pytest.raises(ValueError, match="mode inválido"):
            load_config(p)

    def test_exec_sin_executable_lanza_value_error(self, tmp_path):
        from launcher import load_config
        p = self._ini(tmp_path, "[cmd]\nmode = exec\n")
        with pytest.raises(ValueError, match="executable"):
            load_config(p)

    def test_no_exec_sin_template_lanza_value_error(self, tmp_path):
        from launcher import load_config
        p = self._ini(tmp_path, "[cmd]\nmode = shell\n")
        with pytest.raises(ValueError, match="template"):
            load_config(p)

    def test_param_con_path_true_se_carga(self, tmp_path):
        from launcher import load_config
        p = self._ini(
            tmp_path,
            "[cmd]\nmode = shell\ntemplate = echo {f}\nparams = f\nf.path = true\n",
        )
        cfg = load_config(p)
        assert cfg["commands"]["cmd"]["params"]["f"]["path"] is True
