#Requires -Version 5.1
# Autocompletado nativo para mini-launcher / l (Tab en PowerShell).
# Uso manual:  . "C:\ruta\a\miniLauncher2\launcher-completion.ps1"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$MiniLauncherPython = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $MiniLauncherPython)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cmd) { $MiniLauncherPython = $cmd.Source } else { $MiniLauncherPython = 'python' }
}
$MiniLauncherScript = Join-Path $Root 'launcher.py'

$MiniLauncherCompletionBlock = {
    param(
        [string]$wordToComplete,
        [System.Management.Automation.Language.Ast]$commandAst,
        [int]$cursorPosition
    )
    $line = $commandAst.Extent.Text
    if ($null -eq $line) { return }
    $env:COMP_LINE = $line
    $env:COMP_POINT = [string]$cursorPosition
    & $MiniLauncherPython $MiniLauncherScript --complete 2>$null | ForEach-Object { $_ }
}.GetNewClosure()

Register-ArgumentCompleter -Native -CommandName 'mini-launcher' -ScriptBlock $MiniLauncherCompletionBlock
Register-ArgumentCompleter -Native -CommandName 'l' -ScriptBlock $MiniLauncherCompletionBlock
