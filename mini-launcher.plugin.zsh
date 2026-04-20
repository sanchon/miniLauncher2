# Auto-generado por mini-launcher. No editar manualmente.
# Regenerar con:  mini-launcher --generate-omz-plugin
# Instalar con:   mini-launcher --install-omz-plugin

_mini_launcher_cmd=(/usr/bin/python3.12 /home/hugo/miniLauncher2/launcher.py)

# deploy — Despliega una version en un entorno
function deploy() {
    "${_mini_launcher_cmd[@]}" deploy "$@"
}
_deploy() {
    _arguments \
        '1:env:(dev staging prod)' \
        '--env[env]:env:(dev staging prod)' \
        '2:version: ' \
        '--version[version]:version: '
}
compdef _deploy deploy

# logs — Muestra logs filtrados por servicio y nivel
function logs() {
    "${_mini_launcher_cmd[@]}" logs "$@"
}
_logs() {
    _arguments \
        '1:service:(api worker web)' \
        '--service[service]:service:(api worker web)' \
        '2::level:(info warn error)' \
        '--level[level]:level:(info warn error)'
}
compdef _logs logs

# buscar — Abre una busqueda en el navegador por defecto
function buscar() {
    "${_mini_launcher_cmd[@]}" buscar "$@"
}
_buscar() {
    _arguments \
        '1:termino: ' \
        '--termino[termino]:termino: '
}
compdef _buscar buscar

# abrir — Abre fichero o URL con la app asociada
function abrir() {
    "${_mini_launcher_cmd[@]}" abrir "$@"
}
_abrir() {
    _arguments \
        '1:ruta:_files' \
        '--ruta[ruta]:ruta:_files'
}
compdef _abrir abrir

# git_version — Muestra la version de git (subproceso, sin shell)
function git_version() {
    "${_mini_launcher_cmd[@]}" git_version "$@"
}

# git_log — Ultimas confirmaciones de git (oneline)
function git_log() {
    "${_mini_launcher_cmd[@]}" git_log "$@"
}
_git_log() {
    _arguments \
        '1:n:(1 3 5)' \
        '--n[n]:n:(1 3 5)'
}
compdef _git_log git_log

# neovide_editar — Abre Neovide en un fichero (:e)
function neovide_editar() {
    "${_mini_launcher_cmd[@]}" neovide_editar "$@"
}
_neovide_editar() {
    _arguments \
        '1:fichero:_files' \
        '--fichero[fichero]:fichero:_files'
}
compdef _neovide_editar neovide_editar
