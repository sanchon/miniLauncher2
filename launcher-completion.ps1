#Requires -Version 5.1
# Autocompletado PowerShell: coloca este fichero junto al ejecutable mini-launcher (o launcher.py en desarrollo).
# Uso manual:  . "C:\ruta\launcher-completion.ps1"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

$MiniLauncherExe = $null
$MiniLauncherPython = $null
$MiniLauncherScript = $null

$ExeWin = Join-Path $Root 'mini-launcher.exe'
$ExeUnix = Join-Path $Root 'mini-launcher'

if (Test-Path -LiteralPath $ExeWin) {
    $MiniLauncherExe = (Resolve-Path -LiteralPath $ExeWin).Path
} elseif (Test-Path -LiteralPath $ExeUnix) {
    $MiniLauncherExe = (Resolve-Path -LiteralPath $ExeUnix).Path
} else {
    $MiniLauncherScript = Join-Path $Root 'launcher.py'
    $tryVenv = Join-Path $Root '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $tryVenv)) {
        $tryVenv = Join-Path $Root '.venv/bin/python'
    }
    if (Test-Path -LiteralPath $tryVenv) {
        $MiniLauncherPython = (Resolve-Path -LiteralPath $tryVenv).Path
    } else {
        $cmd = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { $MiniLauncherPython = $cmd.Source } else { $MiniLauncherPython = 'python' }
    }
}

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
    if ($null -ne $MiniLauncherExe) {
        & $MiniLauncherExe --complete 2>$null | ForEach-Object { $_ }
    } else {
        & $MiniLauncherPython $MiniLauncherScript --complete 2>$null | ForEach-Object { $_ }
    }
}.GetNewClosure()

Register-ArgumentCompleter -Native -CommandName 'mini-launcher' -ScriptBlock $MiniLauncherCompletionBlock
Register-ArgumentCompleter -Native -CommandName 'l' -ScriptBlock $MiniLauncherCompletionBlock
