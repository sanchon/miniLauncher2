#!/usr/bin/env zsh
# Autocompletado Zsh: coloca este fichero junto a mini-launcher (o launcher.py en desarrollo).

_mini_launcher_complete() {
  local script_dir="${MINILAUNCHER_HOME:-}"
  if [[ -z "$script_dir" ]]; then
    script_dir="$(cd "$(dirname "${(%):-%x}")" 2>/dev/null && pwd)"
  fi

  local -a runner
  if [[ -f "${script_dir}/mini-launcher" ]]; then
    runner=("${script_dir}/mini-launcher")
  elif [[ -f "${script_dir}/mini-launcher.exe" ]]; then
    runner=("${script_dir}/mini-launcher.exe")
  else
    local py_cmd=""
    if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
      py_cmd="${VIRTUAL_ENV}/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
      py_cmd="python3"
    elif command -v python >/dev/null 2>&1; then
      py_cmd="python"
    else
      return 1
    fi
    runner=("${py_cmd}" "${script_dir}/launcher.py")
  fi

  local raw
  raw="$(COMP_LINE="${BUFFER}" COMP_POINT="${CURSOR}" "${runner[@]}" --complete 2>/dev/null)"

  [[ -z "$raw" ]] && return

  local -a completions
  completions=("${(@f)raw}")
  compadd -Q -- "${completions[@]}"
}

compdef _mini_launcher_complete l
compdef _mini_launcher_complete mini-launcher
compdef _mini_launcher_complete mini-launcher.exe
compdef _mini_launcher_complete launcher
compdef _mini_launcher_complete launcher.py
compdef _mini_launcher_complete ./launcher.py
