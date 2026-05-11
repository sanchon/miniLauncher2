"""Pruebas del sistema de autocompletado (Prioridad 1).

Cubre: _parse_rest_for_completion, completion_candidates_from_words,
path_completion_context, complete_mode y LauncherCompleter.get_completions.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

from launcher import (
    LauncherCompleter,
    _parse_rest_for_completion,
    complete_mode,
    completion_candidates_from_words,
    list_command_names,
    path_completion_context,
)


# ---------------------------------------------------------------------------
# _parse_rest_for_completion
# ---------------------------------------------------------------------------

class TestParseRestForCompletion:

    def test_lista_vacia_devuelve_sin_usados_ni_pendiente(self):
        used, pending = _parse_rest_for_completion([])
        assert used == {}
        assert pending is None

    def test_par_flag_valor_se_asigna(self):
        used, pending = _parse_rest_for_completion(["--env", "dev"])
        assert used == {"env": "dev"}
        assert pending is None

    def test_flag_al_final_queda_pendiente(self):
        used, pending = _parse_rest_for_completion(["--env"])
        assert used == {}
        assert pending == "env"

    def test_formato_key_igual_val(self):
        used, pending = _parse_rest_for_completion(["--env=dev"])
        assert used == {"env": "dev"}
        assert pending is None

    def test_posicional_sin_param_order_no_se_asigna(self):
        used, pending = _parse_rest_for_completion(["valor"])
        assert used == {}

    def test_posicional_con_param_order_asigna_primer_slot(self):
        used, pending = _parse_rest_for_completion(["dev"], ["env", "version"])
        assert used == {"env": "dev"}
        assert pending is None

    def test_dos_posicionales_con_param_order(self):
        used, pending = _parse_rest_for_completion(["dev", "1.0"], ["env", "version"])
        assert used == {"env": "dev", "version": "1.0"}
        assert pending is None

    def test_flag_seguido_de_otro_flag_queda_pendiente_el_segundo(self):
        used, pending = _parse_rest_for_completion(["--env", "--version"])
        assert pending == "version"

    def test_multiples_pares_flag_valor(self):
        used, pending = _parse_rest_for_completion(["--env", "dev", "--version", "1.0"])
        assert used == {"env": "dev", "version": "1.0"}
        assert pending is None

    def test_flag_pendiente_al_final_tras_pares(self):
        used, pending = _parse_rest_for_completion(["--env", "dev", "--version"])
        assert used == {"env": "dev"}
        assert pending == "version"


# ---------------------------------------------------------------------------
# completion_candidates_from_words
# ---------------------------------------------------------------------------

class TestCompletionCandidatesFromWords:

    # -- sin palabras → nombres de comandos
    def test_sin_palabras_devuelve_todos_los_comandos(self, cfg):
        current, candidates = completion_candidates_from_words(cfg, [], False)
        assert current == ""
        assert candidates == list_command_names(cfg)

    # -- una palabra sin espacio → filtrar comandos por prefijo (el filtrado es del completer)
    def test_una_palabra_sin_espacio_devuelve_comandos_con_prefijo_como_current(self, cfg):
        current, candidates = completion_candidates_from_words(cfg, ["dep"], False)
        assert current == "dep"
        assert "deploy" in candidates

    # -- una palabra con espacio → parámetros del comando
    def test_una_palabra_con_espacio_devuelve_parametros(self, cfg):
        current, candidates = completion_candidates_from_words(cfg, ["deploy"], True)
        assert current == ""
        assert "--env" in candidates
        assert "--version" in candidates

    # -- modo posicional: con solo el comando y espacio, la función ofrece flags (no values)
    def test_una_palabra_con_espacio_ofrece_flags_no_values(self, cfg):
        current, candidates = completion_candidates_from_words(cfg, ["deploy"], True)
        assert "--env" in candidates
        assert "dev" not in candidates  # los valores solo aparecen al escribir parcialmente

    # -- modo posicional avanzado: primer slot completado → valores del segundo
    def test_posicional_segundo_slot_sin_choices_devuelve_params_restantes(self, cfg):
        current, candidates = completion_candidates_from_words(cfg, ["deploy", "dev"], True)
        assert "--version" in candidates

    # -- modo posicional: completar valor parcial del primer slot
    def test_posicional_valor_parcial_filtra_choices(self, cfg):
        current, candidates = completion_candidates_from_words(cfg, ["deploy", "d"], False)
        assert current == "d"
        assert "dev" in candidates
        assert "staging" not in candidates

    # -- modo nombrado: --flag completado parcialmente
    def test_flag_parcial_filtra_parametros_disponibles(self, cfg):
        current, candidates = completion_candidates_from_words(cfg, ["deploy", "--en"], False)
        assert "--env" in candidates
        assert "--version" not in candidates

    # -- modo nombrado: valor pendiente tras espacio
    def test_tras_flag_espacio_ofrece_valores_del_param(self, cfg):
        current, candidates = completion_candidates_from_words(
            cfg, ["deploy", "--env"], True
        )
        assert current == ""
        assert "dev" in candidates
        assert "staging" in candidates

    # -- modo nombrado: flag ya usado no se repite
    def test_flag_ya_usado_no_aparece_en_candidatos(self, cfg):
        current, candidates = completion_candidates_from_words(
            cfg, ["deploy", "--env", "dev"], True
        )
        assert "--env" not in candidates
        assert "--version" in candidates

    # -- formato --key=val parcial
    def test_formato_key_igual_val_parcial_filtra_choices(self, cfg):
        current, candidates = completion_candidates_from_words(
            cfg, ["deploy", "--env=d"], False
        )
        assert "--env=dev" in candidates
        assert "--env=staging" not in candidates

    # -- formato --key= con clave desconocida
    def test_formato_key_igual_clave_desconocida_devuelve_vacio(self, cfg):
        current, candidates = completion_candidates_from_words(
            cfg, ["deploy", "--noexiste=v"], False
        )
        assert candidates == []

    # -- parámetro pendiente en modo no-espacio: valor parcial
    def test_pendiente_valor_parcial_filtra_choices(self, cfg):
        current, candidates = completion_candidates_from_words(
            cfg, ["git_log", "--n", ""], False
        )
        # pending="n", current="" → devuelve todos los choices de n
        assert "1" in candidates
        assert "3" in candidates

    # -- comando sin parámetros: no ofrece flags
    def test_comando_sin_params_devuelve_lista_vacia_tras_espacio(self, cfg):
        current, candidates = completion_candidates_from_words(
            cfg, ["sin_descripcion"], True
        )
        assert candidates == []

    # -- comando desconocido
    def test_comando_desconocido_devuelve_lista_vacia(self, cfg):
        current, candidates = completion_candidates_from_words(cfg, ["noexiste"], True)
        assert candidates == []

    # -- param con choices en modo --key=val sin matches
    def test_formato_key_igual_sin_matches_devuelve_vacio(self, cfg):
        current, candidates = completion_candidates_from_words(
            cfg, ["deploy", "--env=xyz"], False
        )
        assert candidates == []

    # -- param sin choices en modo nombrado pendiente no ofrece valores
    def test_param_sin_choices_pendiente_devuelve_vacio(self, cfg):
        current, candidates = completion_candidates_from_words(
            cfg, ["deploy", "--version"], True
        )
        assert candidates == []


# ---------------------------------------------------------------------------
# path_completion_context
# ---------------------------------------------------------------------------

class TestPathCompletionContext:

    def test_texto_vacio_devuelve_none(self, cfg):
        assert path_completion_context(cfg, "") is None

    def test_solo_espacios_devuelve_none(self, cfg):
        assert path_completion_context(cfg, "   ") is None

    def test_comando_desconocido_devuelve_none(self, cfg):
        assert path_completion_context(cfg, "noexiste ") is None

    def test_param_de_tipo_ruta_posicional_con_espacio_devuelve_fragmento_vacio(self, cfg):
        # "abrir " → cursor al inicio del primer slot (ruta), frag = ""
        frag = path_completion_context(cfg, "abrir ")
        assert frag == ""

    def test_param_de_tipo_ruta_posicional_con_valor_parcial(self, cfg):
        frag = path_completion_context(cfg, "abrir /tmp/f")
        assert frag == "/tmp/f"

    def test_param_no_ruta_posicional_devuelve_none(self, cfg):
        # deploy: primer param es env (no es ruta)
        frag = path_completion_context(cfg, "deploy ")
        assert frag is None

    def test_param_ruta_en_modo_named_con_espacio_devuelve_vacio(self, cfg):
        # "abrir --ruta " → pendiente="ruta" (ruta) → frag = ""
        frag = path_completion_context(cfg, "abrir --ruta ")
        assert frag == ""

    def test_param_ruta_en_modo_named_con_valor_parcial(self, cfg):
        frag = path_completion_context(cfg, "abrir --ruta /ho")
        assert frag == "/ho"

    def test_formato_key_igual_val_para_param_ruta(self, cfg):
        frag = path_completion_context(cfg, "abrir --ruta=/tmp/sub")
        assert frag == "/tmp/sub"

    def test_param_no_ruta_en_modo_named_devuelve_none(self, cfg):
        # deploy --env (no path)
        frag = path_completion_context(cfg, "deploy --env ")
        assert frag is None

    def test_editor_fichero_es_ruta(self, cfg):
        frag = path_completion_context(cfg, "editor ")
        assert frag == ""

    def test_param_ruta_pendiente_con_flag_actual_devuelve_none(self, cfg):
        # Si el cursor está sobre un flag (empieza por --), no es ruta
        frag = path_completion_context(cfg, "abrir --ru")
        assert frag is None


# ---------------------------------------------------------------------------
# complete_mode
# ---------------------------------------------------------------------------

class TestCompleteMode:

    def test_sin_comp_line_imprime_todos_los_comandos(self, cfg, capsys, monkeypatch):
        # COMP_LINE vacío → words=[] → devuelve todos los comandos como candidatos
        monkeypatch.delenv("COMP_LINE", raising=False)
        monkeypatch.delenv("COMP_POINT", raising=False)
        rc = complete_mode(cfg)
        assert rc == 0
        out = capsys.readouterr().out
        assert "deploy" in out
        assert "buscar" in out

    def test_comp_line_con_prefijo_imprime_comandos_coincidentes(self, cfg, capsys, monkeypatch):
        line = "mini-launcher dep"
        monkeypatch.setenv("COMP_LINE", line)
        monkeypatch.setenv("COMP_POINT", str(len(line)))
        complete_mode(cfg)
        out = capsys.readouterr().out
        assert "deploy" in out

    def test_comp_line_con_espacio_imprime_params(self, cfg, capsys, monkeypatch):
        line = "mini-launcher deploy "
        monkeypatch.setenv("COMP_LINE", line)
        monkeypatch.setenv("COMP_POINT", str(len(line)))
        complete_mode(cfg)
        out = capsys.readouterr().out
        assert "--env" in out or "dev" in out

    def test_comp_point_trunca_la_linea(self, cfg, capsys, monkeypatch):
        # COMP_POINT en mitad de "deploy" → solo "dep" visible
        monkeypatch.setenv("COMP_LINE", "mini-launcher deploy")
        monkeypatch.setenv("COMP_POINT", "17")  # "mini-launcher dep"
        complete_mode(cfg)
        out = capsys.readouterr().out
        assert "deploy" in out

    def test_devuelve_0(self, cfg, monkeypatch):
        monkeypatch.setenv("COMP_LINE", "mini-launcher ")
        monkeypatch.setenv("COMP_POINT", "14")
        rc = complete_mode(cfg)
        assert rc == 0


# ---------------------------------------------------------------------------
# LauncherCompleter
# ---------------------------------------------------------------------------

class TestLauncherCompleter:

    def test_init_asigna_cfg(self, cfg):
        completer = LauncherCompleter(cfg)
        assert completer.cfg is cfg

    def test_init_crea_path_completer(self, cfg):
        completer = LauncherCompleter(cfg)
        assert completer._path_completer is not None

    def test_get_completions_devuelve_comandos_al_inicio(self, cfg):
        from prompt_toolkit.document import Document
        completer = LauncherCompleter(cfg)
        doc = Document("dep", cursor_position=3)
        completions = list(completer.get_completions(doc, None))
        texts = [c.text for c in completions]
        assert "deploy" in texts

    def test_get_completions_param_ruta_usa_path_completer(self, cfg):
        from prompt_toolkit.document import Document
        completer = LauncherCompleter(cfg)
        doc = Document("abrir /tmp/", cursor_position=10)
        mock_sub = MagicMock(return_value=iter([]))
        completer._path_completer.get_completions = mock_sub
        list(completer.get_completions(doc, None))
        mock_sub.assert_called_once()

    def test_get_completions_param_no_ruta_no_usa_path_completer(self, cfg):
        from prompt_toolkit.document import Document
        completer = LauncherCompleter(cfg)
        doc = Document("deploy ", cursor_position=7)
        mock_sub = MagicMock(return_value=iter([]))
        completer._path_completer.get_completions = mock_sub
        list(completer.get_completions(doc, None))
        mock_sub.assert_not_called()
