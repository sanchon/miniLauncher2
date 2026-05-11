"""Pruebas de las rutas de main() no cubiertas (Prioridades 5 y 6).

Cubre: flags conflictivos, rutas de fallo en install/uninstall,
--complete, --install-omz-plugin, ejecución de comando vía CLI
y arranque de la shell interactiva vía CLI.
"""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from launcher import main


# ---------------------------------------------------------------------------
# Flags conflictivos (líneas 1248, 1250, 1254)
# ---------------------------------------------------------------------------

class TestFlagsConflictivos:

    def test_instalar_y_desinstalar_bash_juntos_da_error(self, runner):
        result = runner.invoke(main, [
            "--install-bash-completion",
            "--uninstall-bash-completion",
        ])
        assert result.exit_code != 0

    def test_instalar_y_desinstalar_bash_muestra_mensaje(self, runner):
        result = runner.invoke(main, [
            "--install-bash-completion",
            "--uninstall-bash-completion",
        ])
        assert "install-bash-completion" in result.output or "uninstall" in result.output.lower()

    def test_instalar_y_desinstalar_powershell_juntos_da_error(self, runner):
        result = runner.invoke(main, [
            "--install-powershell-completion",
            "--uninstall-powershell-completion",
        ])
        assert result.exit_code != 0

    def test_instalar_y_desinstalar_zsh_juntos_da_error(self, runner):
        result = runner.invoke(main, [
            "--install-zsh-completion",
            "--uninstall-zsh-completion",
        ])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# install / uninstall —rutas de éxito vía CLI (cubre línea 1292: return)
# ---------------------------------------------------------------------------

class TestInstallUninstallViaCli:

    def test_install_bash_exito_y_retorna(self, runner, tmp_path):
        bashrc = tmp_path / ".bashrc"
        result = runner.invoke(main, [
            "--install-bash-completion",
            "--bashrc", str(bashrc),
        ])
        assert result.exit_code == 0
        assert bashrc.exists()

    def test_uninstall_bash_exito_y_retorna(self, runner, tmp_path):
        bashrc = tmp_path / ".bashrc"
        # Primero instalar
        runner.invoke(main, ["--install-bash-completion", "--bashrc", str(bashrc)])
        result = runner.invoke(main, [
            "--uninstall-bash-completion",
            "--bashrc", str(bashrc),
        ])
        assert result.exit_code == 0

    def test_install_zsh_exito_y_retorna(self, runner, tmp_path):
        zshrc = tmp_path / ".zshrc"
        result = runner.invoke(main, [
            "--install-zsh-completion",
            "--zshrc", str(zshrc),
        ])
        assert result.exit_code == 0
        assert zshrc.exists()

    def test_uninstall_zsh_exito_y_retorna(self, runner, tmp_path):
        zshrc = tmp_path / ".zshrc"
        runner.invoke(main, ["--install-zsh-completion", "--zshrc", str(zshrc)])
        result = runner.invoke(main, [
            "--uninstall-zsh-completion",
            "--zshrc", str(zshrc),
        ])
        assert result.exit_code == 0

    def test_install_powershell_exito_y_retorna(self, runner, tmp_path):
        profile = tmp_path / "profile.ps1"
        result = runner.invoke(main, [
            "--install-powershell-completion",
            "--powershell-profile", str(profile),
        ])
        assert result.exit_code == 0
        assert profile.exists()

    def test_uninstall_powershell_exito_y_retorna(self, runner, tmp_path):
        profile = tmp_path / "profile.ps1"
        runner.invoke(main, [
            "--install-powershell-completion",
            "--powershell-profile", str(profile),
        ])
        result = runner.invoke(main, [
            "--uninstall-powershell-completion",
            "--powershell-profile", str(profile),
        ])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Rutas de fallo en install/uninstall (líneas 1261–1282)
# ---------------------------------------------------------------------------

class TestInstallUninstallFallo:

    def test_uninstall_bash_falla_si_fichero_no_existe(self, runner, tmp_path):
        result = runner.invoke(main, [
            "--uninstall-bash-completion",
            "--bashrc", str(tmp_path / "no_existe.bashrc"),
        ])
        assert result.exit_code != 0

    def test_uninstall_zsh_falla_si_fichero_no_existe(self, runner, tmp_path):
        result = runner.invoke(main, [
            "--uninstall-zsh-completion",
            "--zshrc", str(tmp_path / "no_existe.zshrc"),
        ])
        assert result.exit_code != 0

    def test_uninstall_powershell_falla_si_fichero_no_existe(self, runner, tmp_path):
        result = runner.invoke(main, [
            "--uninstall-powershell-completion",
            "--powershell-profile", str(tmp_path / "no_existe.ps1"),
        ])
        assert result.exit_code != 0

    def test_install_bash_falla_si_funcion_devuelve_no_cero(self, runner, tmp_path):
        with patch("launcher.install_bashrc", return_value=1):
            result = runner.invoke(main, [
                "--install-bash-completion",
                "--bashrc", str(tmp_path / ".bashrc"),
            ])
        assert result.exit_code != 0

    def test_install_zsh_falla_si_funcion_devuelve_no_cero(self, runner, tmp_path):
        with patch("launcher.install_zshrc", return_value=1):
            result = runner.invoke(main, [
                "--install-zsh-completion",
                "--zshrc", str(tmp_path / ".zshrc"),
            ])
        assert result.exit_code != 0

    def test_install_powershell_falla_si_funcion_devuelve_no_cero(self, runner, tmp_path):
        with patch("launcher.install_powershell_profile", return_value=1):
            result = runner.invoke(main, [
                "--install-powershell-completion",
                "--powershell-profile", str(tmp_path / "profile.ps1"),
            ])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# --complete (línea 1300)
# ---------------------------------------------------------------------------

class TestCompleteCli:

    def test_complete_imprime_comandos_con_prefijo(self, runner, ini_path):
        line = "mini-launcher dep"
        result = runner.invoke(
            main,
            ["--config", str(ini_path), "--complete"],
            env={"COMP_LINE": line, "COMP_POINT": str(len(line))},
        )
        assert result.exit_code == 0
        assert "deploy" in result.output

    def test_complete_sin_prefijo_imprime_todos_los_comandos(self, runner, ini_path):
        line = "mini-launcher "
        result = runner.invoke(
            main,
            ["--config", str(ini_path), "--complete"],
            env={"COMP_LINE": line, "COMP_POINT": str(len(line))},
        )
        assert result.exit_code == 0
        assert "deploy" in result.output
        assert "buscar" in result.output

    def test_complete_devuelve_exit_code_0(self, runner, ini_path):
        result = runner.invoke(
            main,
            ["--config", str(ini_path), "--complete"],
            env={"COMP_LINE": "mini-launcher ", "COMP_POINT": "14"},
        )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# --install-omz-plugin (líneas 1303–1307)
# ---------------------------------------------------------------------------

class TestInstallOmzViaCli:

    def test_install_omz_plugin_via_cli_crea_fichero(self, runner, tmp_path, ini_path):
        with patch("launcher.Path.home", return_value=tmp_path), \
             patch("launcher._add_plugin_to_zshrc", return_value=0):
            result = runner.invoke(main, [
                "--config", str(ini_path),
                "--install-omz-plugin",
            ])
        plugin_file = (
            tmp_path / ".oh-my-zsh" / "custom" / "plugins" / "mini-launcher"
            / "mini-launcher.plugin.zsh"
        )
        assert plugin_file.exists()

    def test_install_omz_plugin_via_cli_exit_code_0(self, runner, tmp_path, ini_path):
        with patch("launcher.Path.home", return_value=tmp_path), \
             patch("launcher._add_plugin_to_zshrc", return_value=0):
            result = runner.invoke(main, [
                "--config", str(ini_path),
                "--install-omz-plugin",
            ])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Ejecución directa de comandos vía CLI (línea 1322)
# ---------------------------------------------------------------------------

class TestEjecutarComandoViaCli:

    def test_comando_valido_ejecuta_y_sale_con_0(self, runner, ini_path):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = runner.invoke(main, [
                "--config", str(ini_path),
                "deploy",
                "--env", "dev",
                "--version", "1.0",
            ])
        assert result.exit_code == 0

    def test_comando_desconocido_sale_con_2(self, runner, ini_path):
        result = runner.invoke(main, [
            "--config", str(ini_path),
            "no_existe",
        ])
        assert result.exit_code == 2

    def test_comando_con_param_requerido_faltante_sale_con_2(self, runner, ini_path):
        result = runner.invoke(main, [
            "--config", str(ini_path),
            "deploy",
        ])
        assert result.exit_code == 2

    def test_comando_posicional_funciona(self, runner, ini_path):
        with patch("launcher.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = runner.invoke(main, [
                "--config", str(ini_path),
                "deploy",
                "dev",
                "1.0",
            ])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Shell interactiva vía CLI (líneas 1319–1320)
# ---------------------------------------------------------------------------

class TestShellInteractivaViaCli:

    def test_sin_comando_lanza_shell_y_sale_con_0(self, runner, ini_path):
        with patch("launcher.run_interactive_shell", return_value=0) as mock_shell:
            result = runner.invoke(main, ["--config", str(ini_path)])
        mock_shell.assert_called_once()
        assert result.exit_code == 0

    def test_sin_comando_shell_recibe_cfg(self, runner, ini_path):
        shells_llamados = []
        def fake_shell(cfg):
            shells_llamados.append(cfg)
            return 0
        with patch("launcher.run_interactive_shell", side_effect=fake_shell):
            runner.invoke(main, ["--config", str(ini_path)])
        assert len(shells_llamados) == 1
        assert "commands" in shells_llamados[0]
