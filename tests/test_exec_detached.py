"""Pruebas de run_exec_detached (Prioridad 3).

La función Popen+threading nunca se ejecuta en los tests existentes
porque todos los tests de exec-detach mockean run_exec_detached completa.
"""
import os
import subprocess
import threading
from unittest.mock import MagicMock, patch

import pytest

from launcher import run_exec_detached


class TestRunExecDetached:

    def test_devuelve_0_en_exito(self):
        with patch("launcher.subprocess.Popen") as mock_popen, \
             patch("launcher.threading.Thread"):
            mock_popen.return_value.wait = MagicMock()
            rc = run_exec_detached(["echo", "hola"])
        assert rc == 0

    def test_popen_se_llama_con_shell_false(self):
        with patch("launcher.subprocess.Popen") as mock_popen, \
             patch("launcher.threading.Thread"):
            run_exec_detached(["echo"])
            _, kwargs = mock_popen.call_args
            assert kwargs["shell"] is False

    def test_popen_redirige_stdin_a_devnull(self):
        with patch("launcher.subprocess.Popen") as mock_popen, \
             patch("launcher.threading.Thread"):
            run_exec_detached(["echo"])
            _, kwargs = mock_popen.call_args
            assert kwargs["stdin"] == subprocess.DEVNULL

    def test_popen_redirige_stdout_a_devnull(self):
        with patch("launcher.subprocess.Popen") as mock_popen, \
             patch("launcher.threading.Thread"):
            run_exec_detached(["echo"])
            _, kwargs = mock_popen.call_args
            assert kwargs["stdout"] == subprocess.DEVNULL

    def test_popen_redirige_stderr_a_devnull(self):
        with patch("launcher.subprocess.Popen") as mock_popen, \
             patch("launcher.threading.Thread"):
            run_exec_detached(["echo"])
            _, kwargs = mock_popen.call_args
            assert kwargs["stderr"] == subprocess.DEVNULL

    def test_en_posix_usa_start_new_session(self):
        with patch("launcher.subprocess.Popen") as mock_popen, \
             patch("launcher.threading.Thread"), \
             patch("launcher.os.name", "posix"):
            run_exec_detached(["echo"])
            _, kwargs = mock_popen.call_args
            assert kwargs.get("start_new_session") is True

    def test_inicia_un_hilo_para_esperar_al_proceso(self):
        with patch("launcher.subprocess.Popen") as mock_popen, \
             patch("launcher.threading.Thread") as mock_thread:
            mock_proc = MagicMock()
            mock_popen.return_value = mock_proc
            run_exec_detached(["echo"])
        mock_thread.assert_called_once()

    def test_el_hilo_es_demonio(self):
        with patch("launcher.subprocess.Popen") as mock_popen, \
             patch("launcher.threading.Thread") as mock_thread:
            mock_proc = MagicMock()
            mock_popen.return_value = mock_proc
            run_exec_detached(["echo"])
        _, kwargs = mock_thread.call_args
        assert kwargs.get("daemon") is True

    def test_el_hilo_apunta_a_proc_wait(self):
        with patch("launcher.subprocess.Popen") as mock_popen, \
             patch("launcher.threading.Thread") as mock_thread:
            mock_proc = MagicMock()
            mock_popen.return_value = mock_proc
            run_exec_detached(["echo"])
        call_kwargs = mock_thread.call_args[1]
        assert call_kwargs.get("target") == mock_proc.wait

    def test_devuelve_1_si_popen_lanza_oserror(self):
        with patch("launcher.subprocess.Popen", side_effect=OSError("ejecutable no encontrado")):
            rc = run_exec_detached(["no_existe_este_binario"])
        assert rc == 1

    def test_oserror_imprime_mensaje_en_stderr(self, capsys):
        with patch("launcher.subprocess.Popen", side_effect=OSError("fallo")):
            run_exec_detached(["no_existe"])
        err = capsys.readouterr().err
        assert "No se pudo" in err

    def test_popen_recibe_el_argv_completo(self):
        argv = ["git", "log", "--oneline"]
        with patch("launcher.subprocess.Popen") as mock_popen, \
             patch("launcher.threading.Thread"):
            run_exec_detached(argv)
        args, _ = mock_popen.call_args
        assert args[0] == argv
