param([string]$Ruta = (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Brave.lnk'))

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Ruta -PathType Leaf)) {
    throw "No existe $Ruta. Indica la ruta de Brave.lnk o brave.exe."
}
$candidate = Get-Item -LiteralPath $Ruta
if ($candidate.Extension -ieq '.lnk') {
    $shell = New-Object -ComObject WScript.Shell
    $target = $shell.CreateShortcut($candidate.FullName).TargetPath
    if (-not $target -or -not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw "El acceso directo no apunta a un archivo existente: $Ruta"
    }
    $candidate = Get-Item -LiteralPath $target
}
if ($candidate.Name -ine 'brave.exe') {
    throw "Se esperaba brave.exe. El destino es $($candidate.Name)."
}
$candidate.FullName
