"""Pruebas de la integración con PowerShell (Prioridad 4).

Cubre: ps_single_quoted, powershell_profile_block_content,
install_powershell_profile, uninstall_powershell_profile.
Los patrones son análogos a los de Bash/Zsh en test_shell_install.py.
"""
from pathlib import Path

import pytest

from launcher import (
    POWERSHELL_BLOCK_END,
    POWERSHELL_BLOCK_START,
    install_powershell_profile,
    powershell_profile_block_content,
    ps_single_quoted,
    uninstall_powershell_profile,
)

APP_DIR = Path("/fake/app")


def write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# ps_single_quoted
# ---------------------------------------------------------------------------

class TestPsSingleQuoted:

    def test_envuelve_en_comillas_simples(self):
        assert ps_single_quoted("hola") == "'hola'"

    def test_cadena_vacia(self):
        assert ps_single_quoted("") == "''"

    def test_escapa_comilla_simple_interna(self):
        assert ps_single_quoted("it's") == "'it''s'"

    def test_escapa_multiples_comillas_simples(self):
        assert ps_single_quoted("a'b'c") == "'a''b''c'"

    def test_no_altera_comillas_dobles(self):
        result = ps_single_quoted('say "hi"')
        assert '"hi"' in result

    def test_ruta_con_backslash(self):
        result = ps_single_quoted(r"C:\Users\foo")
        assert r"C:\Users\foo" in result


# ---------------------------------------------------------------------------
# powershell_profile_block_content
# ---------------------------------------------------------------------------

class TestPowershellProfileBlockContent:

    def test_contiene_marca_de_inicio(self):
        assert POWERSHELL_BLOCK_START in powershell_profile_block_content(APP_DIR)

    def test_contiene_marca_de_fin(self):
        assert POWERSHELL_BLOCK_END in powershell_profile_block_content(APP_DIR)

    def test_contiene_register_argument_completer(self):
        content = powershell_profile_block_content(APP_DIR)
        assert "Register-ArgumentCompleter" in content

    def test_registra_alias_mini_launcher(self):
        content = powershell_profile_block_content(APP_DIR)
        assert "mini-launcher" in content

    def test_registra_alias_l(self):
        content = powershell_profile_block_content(APP_DIR)
        assert "'l'" in content or '"l"' in content or "-CommandName 'l'" in content

    def test_termina_con_newline(self):
        assert powershell_profile_block_content(APP_DIR).endswith("\n")

    def test_no_frozen_referencia_python_y_script(self):
        content = powershell_profile_block_content(APP_DIR)
        assert "$MiniLauncherPython" in content
        assert "$MiniLauncherScript" in content

    def test_no_frozen_no_referencia_exe(self):
        content = powershell_profile_block_content(APP_DIR)
        assert "$MiniLauncherExe" not in content

    def test_contiene_comp_line_para_completado(self):
        content = powershell_profile_block_content(APP_DIR)
        assert "COMP_LINE" in content


# ---------------------------------------------------------------------------
# install_powershell_profile
# ---------------------------------------------------------------------------

class TestInstallPowershellProfile:

    def test_crea_el_fichero_si_no_existe(self, tmp_path):
        profile = tmp_path / "profile.ps1"
        rc = install_powershell_profile(profile)
        assert rc == 0
        assert profile.exists()

    def test_el_fichero_contiene_la_marca_de_inicio(self, tmp_path):
        profile = tmp_path / "profile.ps1"
        install_powershell_profile(profile)
        assert POWERSHELL_BLOCK_START in profile.read_text()

    def test_el_fichero_contiene_la_marca_de_fin(self, tmp_path):
        profile = tmp_path / "profile.ps1"
        install_powershell_profile(profile)
        assert POWERSHELL_BLOCK_END in profile.read_text()

    def test_aniade_bloque_a_fichero_existente_preservando_contenido(self, tmp_path):
        profile = write(tmp_path / "profile.ps1", "# contenido previo\n")
        install_powershell_profile(profile)
        content = profile.read_text()
        assert "# contenido previo" in content
        assert POWERSHELL_BLOCK_START in content

    def test_no_duplica_si_ya_estaba_instalado(self, tmp_path):
        profile = tmp_path / "profile.ps1"
        install_powershell_profile(profile)
        install_powershell_profile(profile)
        assert profile.read_text().count(POWERSHELL_BLOCK_START) == 1

    def test_devuelve_0_en_exito(self, tmp_path):
        assert install_powershell_profile(tmp_path / "profile.ps1") == 0

    def test_devuelve_0_si_ya_estaba_instalado(self, tmp_path):
        profile = tmp_path / "profile.ps1"
        install_powershell_profile(profile)
        assert install_powershell_profile(profile) == 0

    def test_aniade_newline_si_fichero_no_termina_con_newline(self, tmp_path):
        profile = write(tmp_path / "profile.ps1", "# sin newline")
        install_powershell_profile(profile)
        content = profile.read_text()
        assert "# sin newline\n" in content

    def test_crea_directorio_padre_si_no_existe(self, tmp_path):
        profile = tmp_path / "subdir" / "profile.ps1"
        install_powershell_profile(profile)
        assert profile.exists()


# ---------------------------------------------------------------------------
# uninstall_powershell_profile
# ---------------------------------------------------------------------------

class TestUninstallPowershellProfile:

    def test_devuelve_1_si_fichero_no_existe(self, tmp_path):
        assert uninstall_powershell_profile(tmp_path / "profile.ps1") == 1

    def test_devuelve_1_si_bloque_no_esta(self, tmp_path):
        profile = write(tmp_path / "profile.ps1", "# sin bloque\n")
        assert uninstall_powershell_profile(profile) == 1

    def test_devuelve_0_tras_eliminar_bloque(self, tmp_path):
        profile = tmp_path / "profile.ps1"
        install_powershell_profile(profile)
        assert uninstall_powershell_profile(profile) == 0

    def test_elimina_la_marca_de_inicio(self, tmp_path):
        profile = tmp_path / "profile.ps1"
        install_powershell_profile(profile)
        uninstall_powershell_profile(profile)
        assert POWERSHELL_BLOCK_START not in profile.read_text()

    def test_elimina_la_marca_de_fin(self, tmp_path):
        profile = tmp_path / "profile.ps1"
        install_powershell_profile(profile)
        uninstall_powershell_profile(profile)
        assert POWERSHELL_BLOCK_END not in profile.read_text()

    def test_preserva_contenido_antes_del_bloque(self, tmp_path):
        profile = write(tmp_path / "profile.ps1", "# antes\n")
        install_powershell_profile(profile)
        uninstall_powershell_profile(profile)
        assert "# antes" in profile.read_text()

    def test_preserva_contenido_despues_del_bloque(self, tmp_path):
        block = f"{POWERSHELL_BLOCK_START}\nalgo\n{POWERSHELL_BLOCK_END}\n"
        profile = write(tmp_path / "profile.ps1", block + "# despues\n")
        uninstall_powershell_profile(profile)
        assert "# despues" in profile.read_text()

    def test_segundo_uninstall_devuelve_1(self, tmp_path):
        profile = tmp_path / "profile.ps1"
        install_powershell_profile(profile)
        uninstall_powershell_profile(profile)
        assert uninstall_powershell_profile(profile) == 1
