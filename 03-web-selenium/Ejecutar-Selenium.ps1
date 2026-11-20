[CmdletBinding()]
param(
    [ValidateSet('local','render')][string]$Entorno = 'local',
    [string]$Brave = (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Brave.lnk'),
    [string]$Caso,
    [ValidateRange(1024,65535)][int]$PuertoWeb = 4174,
    [switch]$Visible
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'Prepara .venv e instala requirements.txt según la guía de Selenium.'
}
$previousBrave = $env:BRAVE_BINARY
$env:BRAVE_BINARY = & "$root\Resolver-Brave.ps1" -Ruta $Brave
$params = @((Join-Path $root 'ejecutar.py'), '--entorno', $Entorno, '--puerto', "$PuertoWeb")
if ($Caso) { $params += @('--caso', $Caso) }
if ($Visible) { $params += '--visible' }

try {
    if ($Entorno -eq 'local') {
        $fixture = Join-Path (Split-Path $root -Parent) '01-api-karate\Ejecutar-Local.ps1'
        $work = {
            param($api, $directory, $startupMs)
            & $python @params --api-url $api --trabajo $directory
        }.GetNewClosure()
        & $fixture -ApiPort 8013 -PostgresPort 55443 -StoragePort 59113 -Trabajo $work -OrigenAdicional "http://127.0.0.1:$PuertoWeb"
    } else {
        & $python @params
    }
    $result = $LASTEXITCODE
} finally {
    $env:BRAVE_BINARY = $previousBrave
}
exit $result
