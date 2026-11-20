[CmdletBinding()]
param(
    [ValidateRange(1024,65535)][int]$ApiPort = 8011,
    [ValidateRange(1024,65535)][int]$PostgresPort = 55441,
    [ValidateRange(1024,65535)][int]$StoragePort = 59111,
    [switch]$SinDescargas,
    [scriptblock]$Trabajo,
    [string]$OrigenAdicional,
    [ValidateRange(1, [int]::MaxValue)][int]$InferenceThreads = 1
)

$ErrorActionPreference = 'Stop'
$wslDistro = if ($env:VT_QA_WSL_DISTRO) { $env:VT_QA_WSL_DISTRO } else { 'Ubuntu' }
$project = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$backend = Join-Path $project 'VisionText-backend'
$python = Join-Path $backend '.venv\windows\Scripts\python.exe'
$rustfs = Join-Path $backend '.venv\rustfs\rustfs.exe'
$models = Join-Path $backend 'model_cache\onnx'
foreach ($required in @($python, $rustfs, (Join-Path $models 'manifest.json'))) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Falta $required. Prepara el backend local según su README."
    }
}
if ((@($ApiPort, $PostgresPort, $StoragePort) | Sort-Object -Unique).Count -ne 3) {
    throw 'Usa tres puertos distintos para la API, PostgreSQL y S3.'
}
foreach ($port in @($ApiPort, $PostgresPort, $StoragePort)) {
    $check = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
    try { $check.Start() } catch { throw "El puerto local $port no está disponible." } finally { $check.Stop() }
}

function Wait-Ready($Process, [string]$Url, [string]$Log, [int]$Seconds) {
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ($Process.HasExited) { throw "El proceso terminó. Revisa $Log" }
        try {
            return Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2 -ErrorAction Stop
        } catch {
            Start-Sleep -Milliseconds 350
        }
    }
    throw "Tiempo de espera agotado para $Url. Revisa $Log"
}

$runId = [guid]::NewGuid().ToString('N')
$work = Join-Path $PSScriptRoot "target\local-$runId"
New-Item -ItemType Directory -Path (Join-Path $work 'objects') -Force | Out-Null
$baseUrl = "http://127.0.0.1:$ApiPort"
$dbPassword = [guid]::NewGuid().ToString('N')
$storagePassword = [guid]::NewGuid().ToString('N')
$adminPassword = [guid]::NewGuid().ToString('N')
$clusterAttempted = $false
$storage = $null
$api = $null
$result = 1
$corsOrigins = @('http://127.0.0.1:5173', 'http://localhost:5173')
if ($OrigenAdicional) { $corsOrigins += $OrigenAdicional }
$environment = @{
    VT_QA_DB_PASSWORD = $dbPassword
    WSLENV = (@($env:WSLENV, 'VT_QA_DB_PASSWORD') | Where-Object { $_ }) -join ':'
    POSTGRES_URL = ('postgresql+asyncpg://karate:{0}@127.0.0.1:{1}/postgres' -f $dbPassword, $PostgresPort)
    POSTGRES_SSL = 'disable'
    STORAGE_BACKEND = 's3'
    MINIO_ENDPOINT = "127.0.0.1:$StoragePort"
    MINIO_ACCESS_KEY = 'visiontext-karate'
    MINIO_SECRET_KEY = $storagePassword
    MINIO_SECURE = 'false'
    MINIO_BUCKET_IMAGES = 'visiontext-images'
    MINIO_BUCKET_THUMBNAILS = 'visiontext-thumbnails'
    RUSTFS_ACCESS_KEY = 'visiontext-karate'
    RUSTFS_SECRET_KEY = $storagePassword
    RUSTFS_CONSOLE_ENABLE = 'false'
    CLIP_BACKEND = 'onnx'
    CLIP_MODEL = 'ViT-B-32'
    CLIP_PRETRAINED = 'openai'
    ONNX_MODEL_DIR = $models
    ONNX_PRECISION = 'q8f16'
    FAISS_INDEX_PATH = (Join-Path $work 'faiss\index.bin')
    MAX_IMAGE_PIXELS = '4000000'
    THUMBNAIL_SIZE = '256'
    SIMILARITY_THRESHOLD = '0.20'
    INFERENCE_THREADS = [string]$InferenceThreads
    OMP_NUM_THREADS = '1'
    MKL_NUM_THREADS = '1'
    CORS_ORIGINS = $corsOrigins -join ','
    BASE_URL = $baseUrl
    ADMIN_USERNAME = 'visiontext-qa'
    ADMIN_PASSWORD = $adminPassword
    JWT_SECRET_KEY = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
    LOGIN_MAX_ATTEMPTS_PER_IP = '3'
    LOGIN_MAX_ATTEMPTS_PER_USERNAME = '3'
    LOGIN_WINDOW_SECONDS = '8'
    PYTHONIOENCODING = 'utf-8'
    PYTHONUNBUFFERED = '1'
    VT_KARATE_URL = $baseUrl
    VT_KARATE_ASSET_ORIGIN = $baseUrl
    VT_KARATE_CORS_ORIGIN = 'http://127.0.0.1:5173'
    VT_KARATE_ADMIN_USER = 'visiontext-qa'
    VT_KARATE_ADMIN_PASSWORD = $adminPassword
    VT_KARATE_LOCAL_ISOLATED = '1'
    VT_KARATE_LOGIN_ATTEMPTS = '3'
    VT_KARATE_LOGIN_WINDOW_SECONDS = '8'
}
$previous = @{}
foreach ($name in $environment.Keys) {
    $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

Push-Location -LiteralPath $PSScriptRoot
try {
    foreach ($name in $environment.Keys) {
        [Environment]::SetEnvironmentVariable($name, [string]$environment[$name], 'Process')
    }
    $clusterAttempted = $true
    wsl.exe -d $wslDistro --exec bash ./helpers/postgres-qa.sh start $runId $PostgresPort
    if ($LASTEXITCODE -ne 0) { throw "No se pudo iniciar PostgreSQL 16 en $wslDistro." }

    $storageLog = Join-Path $work 'rustfs-error.log'
    $storageCommand = @{
        FilePath = $rustfs
        WorkingDirectory = $work
        WindowStyle = 'Hidden'
        PassThru = $true
        ArgumentList = @('server', '--address', "127.0.0.1:$StoragePort", 'objects')
        RedirectStandardOutput = (Join-Path $work 'rustfs.log')
        RedirectStandardError = $storageLog
    }
    $storage = Start-Process @storageCommand
    Wait-Ready $storage "http://127.0.0.1:$StoragePort/health" $storageLog 20 | Out-Null

    $apiLog = Join-Path $work 'api-error.log'
    $apiCommand = @{
        FilePath = $python
        WorkingDirectory = $work
        WindowStyle = 'Hidden'
        PassThru = $true
        ArgumentList = @('-m', 'uvicorn', 'main:app', '--app-dir', ('"{0}"' -f $backend), '--host', '127.0.0.1', '--port', "$ApiPort")
        RedirectStandardOutput = (Join-Path $work 'api.log')
        RedirectStandardError = $apiLog
    }
    $startup = [Diagnostics.Stopwatch]::StartNew()
    $api = Start-Process @apiCommand
    $ready = Wait-Ready $api "$baseUrl/api/health" $apiLog 75
    $startup.Stop()
    $health = $ready.Content | ConvertFrom-Json
    if ($health.storage_provider -ne 's3' -or $health.images_in_db -ne 0 -or $health.vectors_in_index -ne 0) {
        throw 'La instancia de Karate debe iniciar con S3 y un catálogo vacío.'
    }

    if ($Trabajo) {
        & $Trabajo $baseUrl $work $startup.ElapsedMilliseconds
        $result = $LASTEXITCODE
    } else {
        & "$PSScriptRoot\Ejecutar-Karate.ps1" -Perfil local -SinDescargas:$SinDescargas
        $localResult = $LASTEXITCODE
        & "$PSScriptRoot\Ejecutar-Karate.ps1" -Perfil limite-login -SinDescargas:$SinDescargas
        $rateResult = $LASTEXITCODE
        $result = if ($localResult -ne 0) { $localResult } else { $rateResult }
    }
} finally {
    foreach ($process in @($api, $storage)) {
        if ($process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
            $process.WaitForExit(4000) | Out-Null
        }
    }
    if ($clusterAttempted) {
        wsl.exe -d $wslDistro --exec bash ./helpers/postgres-qa.sh stop $runId $PostgresPort
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Revisa la limpieza de PostgreSQL en ${wslDistro}: /tmp/visiontext-karate-$runId"
            $result = 1
        }
    }
    foreach ($name in $previous.Keys) {
        [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process')
    }
    Pop-Location
}
exit $result
