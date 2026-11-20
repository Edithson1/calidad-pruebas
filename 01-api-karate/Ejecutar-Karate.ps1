[CmdletBinding()]
param(
    [ValidateSet('publico', 'local', 'limite-login')][string]$Perfil = 'publico',
    [switch]$SinDescargas
)

$ErrorActionPreference = 'Stop'
$androidJava = Join-Path $env:ProgramFiles 'Android\Android Studio\jbr'
$jdk = if ($env:VT_KARATE_JAVA_HOME) { $env:VT_KARATE_JAVA_HOME } elseif (
    Test-Path -LiteralPath (Join-Path $androidJava 'bin\javac.exe')
) { $androidJava } else { $env:JAVA_HOME }
if (-not $jdk -or -not (Test-Path -LiteralPath (Join-Path $jdk 'bin\javac.exe'))) {
    throw 'Configura VT_KARATE_JAVA_HOME o JAVA_HOME con un JDK 21.'
}

$maven = $env:VT_KARATE_MAVEN
if (-not $maven) {
    $installed = Get-Command mvn.cmd -ErrorAction SilentlyContinue
    if ($installed) {
        $maven = $installed.Source
    } else {
        $jetBrains = Join-Path $env:ProgramFiles 'JetBrains'
        if (Test-Path -LiteralPath $jetBrains) {
            $maven = Get-ChildItem -LiteralPath $jetBrains -Directory -Filter 'IntelliJ IDEA*' |
                Sort-Object Name -Descending |
                ForEach-Object { Join-Path $_.FullName 'plugins\maven-plugin\lib\maven3\bin\mvn.cmd' } |
                Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
                Select-Object -First 1
        }
    }
}
if (-not $maven -or -not (Test-Path -LiteralPath $maven -PathType Leaf)) {
    throw 'Agrega Maven al PATH o configura VT_KARATE_MAVEN con la ruta de mvn.cmd.'
}

$originalJava = $env:JAVA_HOME
Push-Location -LiteralPath $PSScriptRoot
try {
    $env:JAVA_HOME = $jdk
    $mavenArgs = @('-ntp', '-B', '-Dmaven.repo.local=target/maven-cache', "-Dkarate.env=$Perfil")
    if ($SinDescargas) { $mavenArgs += '-o' }
    & $maven @mavenArgs test
    $result = $LASTEXITCODE
} finally {
    $env:JAVA_HOME = $originalJava
    Pop-Location
}
exit $result
