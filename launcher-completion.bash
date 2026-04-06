#!/usr/bin/env bash
# Autocompletado Git Bash: coloca este fichero junto a mini-launcher (o launcher.py en desarrollo).

_mini_launcher_complete() {
  local cur="${COMP_WORDS[COMP_CWORD]}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  local runner=()
  if [[ -f "${script_dir}/mini-launcher.exe" ]]; then
    runner=("${script_dir}/mini-launcher.exe")
  elif [[ -f "${script_dir}/mini-launcher" ]]; then
    runner=("${script_dir}/mini-launcher")
  else
    local py_cmd=""
    if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/Scripts/python.exe" ]]; then
      py_cmd="${VIRTUAL_ENV}/Scripts/python.exe"
    elif command -v python3 >/dev/null 2>&1; then
      py_cmd="python3"
    elif command -v python >/dev/null 2>&1; then
      py_cmd="python"
    else
      COMPREPLY=()
      return 0
    fi
    runner=("${py_cmd}" "${script_dir}/launcher.py")
  fi

  local suggestions
  suggestions="$(
    COMP_LINE="${COMP_LINE}" \
    COMP_POINT="${COMP_POINT}" \
    "${runner[@]}" --complete 2>/dev/null
  )"

  COMPREPLY=( $(compgen -W "${suggestions}" -- "${cur}") )
}

complete -o default -F _mini_launcher_complete l
complete -o default -F _mini_launcher_complete mini-launcher
complete -o default -F _mini_launcher_complete mini-launcher.exe
complete -o default -F _mini_launcher_complete launcher
complete -o default -F _mini_launcher_complete launcher.py
complete -o default -F _mini_launcher_complete ./launcher.py
