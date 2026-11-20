[CmdletBinding()]
param(
    [ValidateSet('render', 'local')][string]$Entorno = 'render',
    [ValidatePattern('^APP-(0[1-9]|1[01])$')][string]$Caso,
    [string]$Avd = 'VisionText_QA',
    [ValidateRange(5554,5584)][int]$EmulatorPort = 5562,
    [ValidateRange(1024,65535)][int]$AppiumPort = 4723
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$project = Split-Path (Split-Path $root -Parent) -Parent
$android = Join-Path $project 'VisionText-android'
$local = $Entorno -eq 'local'
if (-not $local -and $Caso -in @('APP-10', 'APP-11')) {
    throw "$Caso requiere el perfil local aislado."
}

$run = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 6)
$report = Join-Path $root "reports\$Entorno\$run"
New-Item -ItemType Directory -Path $report -Force | Out-Null
$apk = if ($local) { Join-Path $android 'app\build\outputs\apk\debug\app-debug.apk' }
       else { Join-Path $android 'artifacts\VisionText.apk' }
$env:VT_APP_ENV = $Entorno
$env:VT_APP_AVD = $Avd
$env:VT_APP_REPORT_DIR = $report
$env:VISIONTEXT_APK = $apk
$env:PYTHONUTF8 = '1'

$testArgs = @(
    '-m', 'pytest', '-v',
    '--html', (Join-Path $report 'reporte.html'), '--self-contained-html',
    '--junitxml', (Join-Path $report 'junit.xml')
)
if (-not $local) { $testArgs += @('-m', 'not solo_local') }
if ($Caso) { $testArgs += @('-k', $Caso.Replace('-', '_')) }
$tests = {
    param($python)
    Push-Location -LiteralPath $root
    try {
        & $python @testArgs
    } finally {
        Pop-Location
    }
}.GetNewClosure()

$verifier = Join-Path $root 'Verificar-Appium.ps1'
$launch = @{
    Avd = $Avd
    EmulatorPort = $EmulatorPort
    AppiumPort = $AppiumPort
    LogDir = (Join-Path $report 'logs')
    Trabajo = $tests
}
Write-Host "Resultados en $report"
if ($local) {
    $env:JAVA_HOME = Join-Path $env:ProgramFiles 'Android\Android Studio\jbr'
    $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
    Push-Location -LiteralPath $android
    try {
        & .\gradlew.bat assembleDebug --no-daemon
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar la APK debug.' }
    } finally {
        Pop-Location
    }
    $backend = Join-Path (Split-Path $root -Parent) '01-api-karate\Ejecutar-Local.ps1'
    $mobile = { & $verifier @launch }.GetNewClosure()
    & $backend -ApiPort 8014 -PostgresPort 55444 -StoragePort 59114 -Trabajo $mobile
} else {
    & $verifier @launch
}
exit $LASTEXITCODE
