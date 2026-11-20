[CmdletBinding()]
param(
    [string]$Avd = 'VisionText_QA',
    [ValidateRange(5554,5584)][int]$EmulatorPort = 5562,
    [ValidateRange(1024,65535)][int]$AppiumPort = 4723,
    [string]$LogDir = (Join-Path $PSScriptRoot 'target'),
    [scriptblock]$Trabajo
)

$ErrorActionPreference = 'Stop'
if ($EmulatorPort % 2) { throw 'El puerto del emulador debe ser par.' }

$root = $PSScriptRoot
$sdk = Join-Path $env:LOCALAPPDATA 'Android\Sdk'
$jdk = Join-Path $env:ProgramFiles 'Android\Android Studio\jbr'
$node = Join-Path $env:LOCALAPPDATA 'nvm\v22.16.0'
$adb = Join-Path $sdk 'platform-tools\adb.exe'
$emulatorExe = Join-Path $sdk 'emulator\emulator.exe'
$appium = Join-Path $root 'node_modules\appium\index.js'
$python = Join-Path $root '.venv\Scripts\python.exe'
foreach ($file in @($adb, $emulatorExe, (Join-Path $node 'node.exe'), $appium, $python)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Falta $file. Consulta la guía de Appium." }
}
foreach ($port in @($EmulatorPort, ($EmulatorPort + 1), $AppiumPort)) {
    $check = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $port)
    try { $check.Start() } catch { throw "El puerto $port está ocupado." } finally { $check.Stop() }
}

$env:ANDROID_HOME = $sdk
$env:ANDROID_SDK_ROOT = $sdk
$env:JAVA_HOME = $jdk
$env:Path = "$node;$jdk\bin;$sdk\platform-tools;$env:Path"
$env:APPIUM_HOME = Join-Path $root '.appium'
$env:VISIONTEXT_ANDROID_UDID = "emulator-$EmulatorPort"
$env:VISIONTEXT_APPIUM_URL = "http://127.0.0.1:$AppiumPort"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$work = (Resolve-Path -LiteralPath $LogDir).Path
$previousAvdHome = $env:ANDROID_AVD_HOME
if ($Avd -eq 'VisionText_QA') {
    $env:ANDROID_AVD_HOME = Join-Path $root 'target\avd'
}
$emu = $null
$server = $null
$code = 1

try {
    if ($Avd -eq 'VisionText_QA' -and -not (Test-Path -LiteralPath (Join-Path $env:ANDROID_AVD_HOME "$Avd.ini"))) {
        $manager = Join-Path $sdk 'cmdline-tools\latest\bin\avdmanager.bat'
        if (-not (Test-Path -LiteralPath $manager)) { throw 'Faltan las herramientas de Android SDK. Consulta la guía de Appium.' }
        New-Item -Path $env:ANDROID_AVD_HOME -ItemType Directory -Force | Out-Null
        'no' | & $manager create avd --name $Avd --package 'system-images;android-34;default;x86_64' --device pixel_5
        if ($LASTEXITCODE) { throw 'No se pudo crear el emulador de pruebas con Android 14.' }
    }
    Write-Host "Iniciando $Avd en $env:VISIONTEXT_ANDROID_UDID..."
    $emuOptions = @{
        FilePath=$emulatorExe; PassThru=$true; WindowStyle='Hidden'
        ArgumentList=@('-avd', $Avd, '-port', "$EmulatorPort", '-read-only', '-no-snapshot', '-no-window', '-no-audio', '-no-boot-anim', '-gpu', 'host')
        RedirectStandardOutput=(Join-Path $work 'emulador.log')
        RedirectStandardError=(Join-Path $work 'emulador-error.log')
    }
    $emu = Start-Process @emuOptions
    $serial = $env:VISIONTEXT_ANDROID_UDID
    $ready = $false
    $deadline = [Diagnostics.Stopwatch]::StartNew()
    while ($deadline.Elapsed.TotalSeconds -lt 180) {
        if ($emu.HasExited) { break }
        $attached = & $adb devices
        if ($attached -match "^$serial\s+device$") {
            if ((& $adb -s $serial shell getprop sys.boot_completed | Out-String).Trim() -eq '1') {
                $ready = $true
                break
            }
        }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw "Android no terminó de arrancar. Revisa las bitácoras en $work." }

    Write-Host 'Android arrancó. Iniciando Appium...'
    $serverOptions = @{
        FilePath=(Join-Path $node 'node.exe'); PassThru=$true; WindowStyle='Hidden'
        ArgumentList=@(
            ('"{0}"' -f $appium), '--address', '127.0.0.1', '--port', "$AppiumPort",
            '--log-level', 'info', '--log-no-colors', '--log-timestamp',
            '--log-filters', ('"{0}"' -f (Join-Path $root 'config\filtros-appium.json'))
        )
        RedirectStandardOutput=(Join-Path $work 'appium.log')
        RedirectStandardError=(Join-Path $work 'appium-error.log')
    }
    $server = Start-Process @serverOptions
    $ready = $false
    for ($i=0; $i -lt 30; $i++) {
        if ($server.HasExited) { break }
        try {
            if ((Invoke-RestMethod "$env:VISIONTEXT_APPIUM_URL/status" -TimeoutSec 2).value.ready) {
                $ready = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) { throw "Appium no estuvo disponible. Revisa las bitácoras en $work." }
    if ($Trabajo) {
        & $Trabajo $python
    } else {
        & $python (Join-Path $root 'comprobar_appium.py')
    }
    $code = $LASTEXITCODE
} finally {
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id }
    if ($emu -and -not $emu.HasExited) {
        if ((& $adb devices) -match "^$($env:VISIONTEXT_ANDROID_UDID)\s+") {
            & $adb -s $env:VISIONTEXT_ANDROID_UDID emu kill | Out-Null
        }
        if (-not $emu.HasExited -and -not $emu.WaitForExit(4000)) { Stop-Process -Id $emu.Id }
    }
    $env:ANDROID_AVD_HOME = $previousAvdHome
}
exit $code
