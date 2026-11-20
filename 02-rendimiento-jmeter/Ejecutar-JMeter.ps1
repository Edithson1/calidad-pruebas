[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('local','render')][string]$Entorno,
    [string[]]$Perfil,
    [string]$JMeterHome = $env:JMETER_HOME,
    [string]$JavaHome = $env:VT_JMETER_JAVA_HOME,
    [ValidateRange(1024,65535)][int]$ApiPort = 8012,
    [ValidateRange(1024,65535)][int]$WebPort = 4173,
    [switch]$SoloPublico,
    [ValidateRange(1, [int]::MaxValue)][int]$HilosInferencia = 1
)

$ErrorActionPreference = 'Stop'
if ($Entorno -eq 'render' -and $PSBoundParameters.ContainsKey('HilosInferencia')) {
    throw '-HilosInferencia se usa con el backend local.'
}
$root = $PSScriptRoot
$project = Split-Path (Split-Path $root -Parent) -Parent
$python = Join-Path $project 'VisionText-backend\.venv\windows\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Falta el entorno Python preparado del backend de VisionText.'
}
if (-not $JMeterHome) {
    $JMeterHome = Join-Path $env:USERPROFILE 'Downloads\apache-jmeter-5.6.3\apache-jmeter-5.6.3'
}
if (-not $JavaHome) {
    $JavaHome = Join-Path $env:ProgramFiles 'Android\Android Studio\jbr'
}
$jar = Join-Path $JMeterHome 'bin\ApacheJMeter.jar'
$java = Join-Path $JavaHome 'bin\java.exe'
foreach ($required in @($jar, $java)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Falta $required. Indica -JMeterHome o -JavaHome."
    }
}
$driver = Join-Path $root 'scripts\ejecutar.py'
$params = @($driver, '--entorno', $Entorno, '--java', $java, '--jmeter', $jar, '--web-port', "$WebPort")
foreach ($name in $Perfil) { $params += @('--perfil', $name) }
if ($SoloPublico) {
    if ($Entorno -ne 'render') { throw '-SoloPublico se usa con Render.' }
    $params += '--solo-publico'
}
if ($Entorno -eq 'local') {
    $work = {
        param($apiUrl, $workingFolder, $startMs)
        & $python @params --api-url $apiUrl --trabajo $workingFolder --arranque-ms $startMs
    }.GetNewClosure()
    $fixtureRunner = Join-Path (Split-Path $root -Parent) '01-api-karate\Ejecutar-Local.ps1'
    & $fixtureRunner -ApiPort $ApiPort -PostgresPort 55442 -StoragePort 59112 -InferenceThreads $HilosInferencia `
        -Trabajo $work -OrigenAdicional "http://127.0.0.1:$WebPort"
} else {
    & $python @params
}
exit $LASTEXITCODE
