param(
    [switch]$OneFile,
    [ValidateSet('x86', 'x64')][string]$Architecture = 'x64',
    [string]$Python = 'python',
    [string]$Tag = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$originalPath = $env:PATH
$pythonExecutable = (Get-Command $Python -ErrorAction Stop).Source
$pythonDirectory = Split-Path -Parent $pythonExecutable
# Prevent unrelated tools on PATH from supplying incompatible same-named DLLs
# (for example Poppler's ICU instead of the Windows ICU used by Qt).
$env:PATH = "$pythonDirectory;$pythonDirectory\Scripts;$env:SystemRoot\System32;$env:SystemRoot;$env:SystemRoot\System32\WindowsPowerShell\v1.0"
Push-Location $projectRoot
try {
    $metadataArguments = @('--architecture', $Architecture)
    if ($Tag) { $metadataArguments += @('--tag', $Tag) }
    & $pythonExecutable scripts/build_metadata.py @metadataArguments
    if ($LASTEXITCODE -ne 0) { throw 'Invalid release version or interpreter architecture.' }
    & $pythonExecutable -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed; build stopped.' }
    & $pythonExecutable scripts/create_assets.py
    if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed.' }
    Copy-Item -LiteralPath README.md -Destination assets/README.md -Force
    $buildMode = if ($OneFile) { '--onefile' } else { '--onedir' }
    $qtBinding = if ($Architecture -eq 'x86') { 'PySide2' } else { 'PySide6' }
    $otherBinding = if ($Architecture -eq 'x86') { 'PySide6' } else { 'PySide2' }
    & $pythonExecutable -m PyInstaller --noconfirm --clean $buildMode --windowed --name NetDirector --distpath "dist/$Architecture" --workpath "build/$Architecture" --icon assets/netdirector.ico --version-file build/version_info.txt --add-data 'assets;assets' --add-data 'VERSION;.' --exclude-module $otherBinding --exclude-module PyQt5 --exclude-module PyQt6 --exclude-module "$qtBinding.QtWebEngineCore" --exclude-module "$qtBinding.QtWebEngineWidgets" --exclude-module "$qtBinding.QtQml" --exclude-module "$qtBinding.QtQuick" main.py
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
    & $pythonExecutable scripts/fetch_forcebindip.py
    if ($LASTEXITCODE -ne 0) { throw 'ForceBindIP fetch failed.' }
    if (-not $OneFile) {
        $distForceBind = Join-Path $projectRoot "dist\$Architecture\NetDirector\ForceBindIP"
        New-Item -ItemType Directory -Path $distForceBind -Force | Out-Null
        Copy-Item -Path (Join-Path $projectRoot "build\ForceBindIP\*") -Destination $distForceBind -Force
    }
    Write-Host "Build complete. Output: dist/$Architecture. Keep the entire NetDirector folder together."
} finally {
    $env:PATH = $originalPath
    Pop-Location
}
