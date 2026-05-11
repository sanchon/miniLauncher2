"""Pruebas de la integración con Bash, Zsh y oh-my-zsh."""
from pathlib import Path
from unittest.mock import patch

import pytest

from launcher import (
    BASHRC_BLOCK_END,
    BASHRC_BLOCK_START,
    ZSHRC_BLOCK_END,
    ZSHRC_BLOCK_START,
    _add_plugin_to_zshrc,
    bashrc_block_content,
    generate_omz_plugin_content,
    install_bashrc,
    install_omz_plugin,
    install_zshrc,
    uninstall_bashrc,
    uninstall_zshrc,
    zshrc_block_content,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


APP_DIR = Path("/fake/app")
LAUNCHER_ARGV = ["/fake/app/mini-launcher"]


# ---------------------------------------------------------------------------
# bashrc_block_content
# ---------------------------------------------------------------------------

class TestBashrcBlockContent:

    def test_contiene_marca_de_inicio(self):
        assert BASHRC_BLOCK_START in bashrc_block_content(APP_DIR)

    def test_contiene_marca_de_fin(self):
        assert BASHRC_BLOCK_END in bashrc_block_content(APP_DIR)

    def test_exporta_minilauncher_home(self):
        assert "MINILAUNCHER_HOME" in bashrc_block_content(APP_DIR)

    def test_define_alias_mini_launcher(self):
        assert "alias mini-launcher=" in bashrc_block_content(APP_DIR)

    def test_referencia_al_script_de_completion(self):
        assert "launcher-completion.bash" in bashrc_block_content(APP_DIR)

    def test_contiene_source(self):
        assert "source" in bashrc_block_content(APP_DIR)

    def test_termina_con_newline(self):
        assert bashrc_block_content(APP_DIR).endswith("\n")


# ---------------------------------------------------------------------------
# install_bashrc
# ---------------------------------------------------------------------------

class TestInstallBashrc:

    def test_crea_el_fichero_si_no_existe(self, tmp_path):
        rc_path = tmp_path / ".bashrc"
        assert install_bashrc(rc_path) == 0
        assert rc_path.exists()

    def test_el_fichero_creado_contiene_el_bloque(self, tmp_path):
        rc_path = tmp_path / ".bashrc"
        install_bashrc(rc_path)
        content = rc_path.read_text()
        assert BASHRC_BLOCK_START in content
        assert BASHRC_BLOCK_END in content

    def test_añade_bloque_a_fichero_existente(self, tmp_path):
        rc_path = write(tmp_path / ".bashrc", "# contenido previo\n")
        install_bashrc(rc_path)
        content = rc_path.read_text()
        assert "# contenido previo" in content
        assert BASHRC_BLOCK_START in content

    def test_preserva_contenido_previo(self, tmp_path):
        rc_path = write(tmp_path / ".bashrc", "export FOO=bar\n")
        install_bashrc(rc_path)
        assert "export FOO=bar" in rc_path.read_text()

    def test_no_duplica_si_ya_esta_instalado(self, tmp_path):
        rc_path = tmp_path / ".bashrc"
        install_bashrc(rc_path)
        install_bashrc(rc_path)
        content = rc_path.read_text()
        assert content.count(BASHRC_BLOCK_START) == 1

    def test_añade_newline_si_fichero_no_termina_con_newline(self, tmp_path):
        rc_path = write(tmp_path / ".bashrc", "export FOO=bar")  # sin \n
        install_bashrc(rc_path)
        content = rc_path.read_text()
        assert "export FOO=bar\n" in content

    def test_devuelve_0_en_exito(self, tmp_path):
        assert install_bashrc(tmp_path / ".bashrc") == 0

    def test_devuelve_0_si_ya_estaba_instalado(self, tmp_path):
        rc_path = tmp_path / ".bashrc"
        install_bashrc(rc_path)
        assert install_bashrc(rc_path) == 0


# ---------------------------------------------------------------------------
# uninstall_bashrc
# ---------------------------------------------------------------------------

class TestUninstallBashrc:

    def test_devuelve_1_si_fichero_no_existe(self, tmp_path):
        assert uninstall_bashrc(tmp_path / ".bashrc") == 1

    def test_devuelve_1_si_bloque_no_esta(self, tmp_path):
        rc_path = write(tmp_path / ".bashrc", "# sin bloque\n")
        assert uninstall_bashrc(rc_path) == 1

    def test_devuelve_0_tras_eliminar_bloque(self, tmp_path):
        rc_path = tmp_path / ".bashrc"
        install_bashrc(rc_path)
        assert uninstall_bashrc(rc_path) == 0

    def test_elimina_la_marca_de_inicio(self, tmp_path):
        rc_path = tmp_path / ".bashrc"
        install_bashrc(rc_path)
        uninstall_bashrc(rc_path)
        assert BASHRC_BLOCK_START not in rc_path.read_text()

    def test_elimina_la_marca_de_fin(self, tmp_path):
        rc_path = tmp_path / ".bashrc"
        install_bashrc(rc_path)
        uninstall_bashrc(rc_path)
        assert BASHRC_BLOCK_END not in rc_path.read_text()

    def test_preserva_contenido_antes_del_bloque(self, tmp_path):
        rc_path = write(tmp_path / ".bashrc", "# antes\n")
        install_bashrc(rc_path)
        uninstall_bashrc(rc_path)
        assert "# antes" in rc_path.read_text()

    def test_preserva_contenido_despues_del_bloque(self, tmp_path):
        block = f"{BASHRC_BLOCK_START}\nalgo\n{BASHRC_BLOCK_END}\n"
        rc_path = write(tmp_path / ".bashrc", block + "# despues\n")
        uninstall_bashrc(rc_path)
        assert "# despues" in rc_path.read_text()

    def test_segundo_uninstall_devuelve_1(self, tmp_path):
        rc_path = tmp_path / ".bashrc"
        install_bashrc(rc_path)
        uninstall_bashrc(rc_path)
        assert uninstall_bashrc(rc_path) == 1


# ---------------------------------------------------------------------------
# zshrc_block_content
# ---------------------------------------------------------------------------

class TestZshrcBlockContent:

    def test_contiene_marca_de_inicio(self):
        assert ZSHRC_BLOCK_START in zshrc_block_content(APP_DIR)

    def test_contiene_marca_de_fin(self):
        assert ZSHRC_BLOCK_END in zshrc_block_content(APP_DIR)

    def test_exporta_minilauncher_home(self):
        assert "MINILAUNCHER_HOME" in zshrc_block_content(APP_DIR)

    def test_define_alias_mini_launcher(self):
        assert "alias mini-launcher=" in zshrc_block_content(APP_DIR)

    def test_referencia_al_script_de_completion(self):
        assert "launcher-completion.zsh" in zshrc_block_content(APP_DIR)

    def test_contiene_guard_de_compinit(self):
        assert "compinit" in zshrc_block_content(APP_DIR)

    def test_termina_con_newline(self):
        assert zshrc_block_content(APP_DIR).endswith("\n")


# ---------------------------------------------------------------------------
# install_zshrc / uninstall_zshrc  (mismos patrones que bash)
# ---------------------------------------------------------------------------

class TestInstallZshrc:

    def test_crea_el_fichero_si_no_existe(self, tmp_path):
        rc_path = tmp_path / ".zshrc"
        assert install_zshrc(rc_path) == 0
        assert rc_path.exists()

    def test_el_fichero_contiene_el_bloque(self, tmp_path):
        rc_path = tmp_path / ".zshrc"
        install_zshrc(rc_path)
        content = rc_path.read_text()
        assert ZSHRC_BLOCK_START in content
        assert ZSHRC_BLOCK_END in content

    def test_preserva_contenido_previo(self, tmp_path):
        rc_path = write(tmp_path / ".zshrc", "export BAR=baz\n")
        install_zshrc(rc_path)
        assert "export BAR=baz" in rc_path.read_text()

    def test_no_duplica_si_ya_esta_instalado(self, tmp_path):
        rc_path = tmp_path / ".zshrc"
        install_zshrc(rc_path)
        install_zshrc(rc_path)
        assert rc_path.read_text().count(ZSHRC_BLOCK_START) == 1

    def test_devuelve_0_en_exito(self, tmp_path):
        assert install_zshrc(tmp_path / ".zshrc") == 0


class TestUninstallZshrc:

    def test_devuelve_1_si_fichero_no_existe(self, tmp_path):
        assert uninstall_zshrc(tmp_path / ".zshrc") == 1

    def test_devuelve_1_si_bloque_no_esta(self, tmp_path):
        rc_path = write(tmp_path / ".zshrc", "# sin bloque\n")
        assert uninstall_zshrc(rc_path) == 1

    def test_devuelve_0_tras_eliminar_bloque(self, tmp_path):
        rc_path = tmp_path / ".zshrc"
        install_zshrc(rc_path)
        assert uninstall_zshrc(rc_path) == 0

    def test_elimina_ambas_marcas(self, tmp_path):
        rc_path = tmp_path / ".zshrc"
        install_zshrc(rc_path)
        uninstall_zshrc(rc_path)
        content = rc_path.read_text()
        assert ZSHRC_BLOCK_START not in content
        assert ZSHRC_BLOCK_END not in content

    def test_preserva_contenido_antes_y_despues(self, tmp_path):
        block = f"{ZSHRC_BLOCK_START}\nalgo\n{ZSHRC_BLOCK_END}\n"
        rc_path = write(tmp_path / ".zshrc", "# antes\n" + block + "# despues\n")
        uninstall_zshrc(rc_path)
        content = rc_path.read_text()
        assert "# antes" in content
        assert "# despues" in content

    def test_segundo_uninstall_devuelve_1(self, tmp_path):
        rc_path = tmp_path / ".zshrc"
        install_zshrc(rc_path)
        uninstall_zshrc(rc_path)
        assert uninstall_zshrc(rc_path) == 1


# ---------------------------------------------------------------------------
# generate_omz_plugin_content
# ---------------------------------------------------------------------------

class TestGenerateOmzPluginContent:

    def test_contiene_funcion_mini_launcher(self, cfg):
        content = generate_omz_plugin_content(cfg, LAUNCHER_ARGV)
        assert "function mini-launcher()" in content

    def test_mini_launcher_cmd_usa_launcher_argv(self, cfg):
        content = generate_omz_plugin_content(cfg, LAUNCHER_ARGV)
        assert "/fake/app/mini-launcher" in content

    def test_mini_launcher_cmd_no_esta_hardcodeado(self, cfg):
        argv = ["/otro/path/mini-launcher"]
        content = generate_omz_plugin_content(cfg, argv)
        assert "/otro/path/mini-launcher" in content
        assert "/fake/app/mini-launcher" not in content

    def test_contiene_funcion_wrapper_por_cada_comando(self, cfg):
        content = generate_omz_plugin_content(cfg, LAUNCHER_ARGV)
        for cmd in ("deploy", "buscar", "abrir", "git_log"):
            assert f"function {cmd}()" in content

    def test_comandos_con_choices_los_incluyen_en_arguments(self, cfg):
        content = generate_omz_plugin_content(cfg, LAUNCHER_ARGV)
        assert "dev" in content
        assert "staging" in content
        assert "prod" in content

    def test_comandos_con_path_usan_files(self, cfg):
        content = generate_omz_plugin_content(cfg, LAUNCHER_ARGV)
        assert "_files" in content

    def test_comandos_con_params_tienen_funcion_de_completado(self, cfg):
        content = generate_omz_plugin_content(cfg, LAUNCHER_ARGV)
        assert "_deploy()" in content
        assert "compdef _deploy deploy" in content

    def test_comandos_sin_params_no_tienen_funcion_de_completado(self, cfg):
        content = generate_omz_plugin_content(cfg, LAUNCHER_ARGV)
        # sin_descripcion no tiene params
        assert "_sin_descripcion()" not in content

    def test_contiene_cabecera_de_no_editar(self, cfg):
        content = generate_omz_plugin_content(cfg, LAUNCHER_ARGV)
        assert "No editar manualmente" in content


# ---------------------------------------------------------------------------
# _add_plugin_to_zshrc
# ---------------------------------------------------------------------------

class TestAddPluginToZshrc:

    def test_devuelve_1_si_fichero_no_existe(self, tmp_path):
        assert _add_plugin_to_zshrc(tmp_path / ".zshrc", "mini-launcher") == 1

    def test_devuelve_1_si_no_hay_linea_plugins(self, tmp_path):
        rc_path = write(tmp_path / ".zshrc", "export ZSH=$HOME/.oh-my-zsh\n")
        assert _add_plugin_to_zshrc(rc_path, "mini-launcher") == 1

    def test_devuelve_0_si_ya_estaba_el_plugin(self, tmp_path):
        rc_path = write(tmp_path / ".zshrc", "plugins=(git mini-launcher)\n")
        assert _add_plugin_to_zshrc(rc_path, "mini-launcher") == 0

    def test_no_duplica_si_ya_estaba(self, tmp_path):
        rc_path = write(tmp_path / ".zshrc", "plugins=(git mini-launcher)\n")
        _add_plugin_to_zshrc(rc_path, "mini-launcher")
        assert rc_path.read_text().count("mini-launcher") == 1

    def test_añade_plugin_en_formato_inline(self, tmp_path):
        rc_path = write(tmp_path / ".zshrc", "plugins=(git zsh-autosuggestions)\n")
        _add_plugin_to_zshrc(rc_path, "mini-launcher")
        assert "mini-launcher" in rc_path.read_text()

    def test_formato_inline_no_rompe_los_parentesis(self, tmp_path):
        rc_path = write(tmp_path / ".zshrc", "plugins=(git)\n")
        _add_plugin_to_zshrc(rc_path, "mini-launcher")
        content = rc_path.read_text()
        assert content.count("(") == 1
        assert content.count(")") == 1

    def test_añade_plugin_en_formato_multilinea(self, tmp_path):
        rc_path = write(tmp_path / ".zshrc", "plugins=(\n  git\n  zsh-autosuggestions\n)\n")
        _add_plugin_to_zshrc(rc_path, "mini-launcher")
        assert "mini-launcher" in rc_path.read_text()

    def test_formato_multilinea_respeta_la_indentacion(self, tmp_path):
        rc_path = write(tmp_path / ".zshrc", "plugins=(\n  git\n)\n")
        _add_plugin_to_zshrc(rc_path, "mini-launcher")
        lines = rc_path.read_text().splitlines()
        ml_line = next(l for l in lines if "mini-launcher" in l)
        assert ml_line.startswith("  ")

    def test_devuelve_0_tras_anadir_el_plugin(self, tmp_path):
        rc_path = write(tmp_path / ".zshrc", "plugins=(git)\n")
        assert _add_plugin_to_zshrc(rc_path, "mini-launcher") == 0


# ---------------------------------------------------------------------------
# install_omz_plugin
# ---------------------------------------------------------------------------

class TestInstallOmzPlugin:

    def test_crea_el_directorio_del_plugin(self, tmp_path, cfg):
        with patch("launcher.Path.home", return_value=tmp_path), \
             patch("launcher._add_plugin_to_zshrc", return_value=0):
            install_omz_plugin(cfg, LAUNCHER_ARGV)
        plugin_dir = tmp_path / ".oh-my-zsh" / "custom" / "plugins" / "mini-launcher"
        assert plugin_dir.is_dir()

    def test_crea_el_fichero_plugin_zsh(self, tmp_path, cfg):
        with patch("launcher.Path.home", return_value=tmp_path), \
             patch("launcher._add_plugin_to_zshrc", return_value=0):
            install_omz_plugin(cfg, LAUNCHER_ARGV)
        plugin_file = tmp_path / ".oh-my-zsh" / "custom" / "plugins" / "mini-launcher" / "mini-launcher.plugin.zsh"
        assert plugin_file.exists()

    def test_el_fichero_contiene_contenido_valido(self, tmp_path, cfg):
        with patch("launcher.Path.home", return_value=tmp_path), \
             patch("launcher._add_plugin_to_zshrc", return_value=0):
            install_omz_plugin(cfg, LAUNCHER_ARGV)
        plugin_file = tmp_path / ".oh-my-zsh" / "custom" / "plugins" / "mini-launcher" / "mini-launcher.plugin.zsh"
        content = plugin_file.read_text()
        assert "function mini-launcher()" in content

    def test_llama_a_add_plugin_to_zshrc(self, tmp_path, cfg):
        with patch("launcher.Path.home", return_value=tmp_path), \
             patch("launcher._add_plugin_to_zshrc", return_value=0) as mock_add:
            install_omz_plugin(cfg, LAUNCHER_ARGV)
        mock_add.assert_called_once()
        assert mock_add.call_args[0][1] == "mini-launcher"

    def test_devuelve_el_codigo_de_add_plugin(self, tmp_path, cfg):
        with patch("launcher.Path.home", return_value=tmp_path), \
             patch("launcher._add_plugin_to_zshrc", return_value=1):
            rc = install_omz_plugin(cfg, LAUNCHER_ARGV)
        assert rc == 1
