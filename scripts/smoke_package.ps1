param([string]$Executable = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Executable) { $Executable = Join-Path $projectRoot 'dist\x64\NetDirector\NetDirector.exe' }
$Executable = (Resolve-Path -LiteralPath $Executable).Path
$previousDataRoot = $env:NETDIRECTOR_DATA_DIR
$testRoot = Join-Path $projectRoot ('.packaged-smoke-' + [guid]::NewGuid().ToString('N'))
$env:NETDIRECTOR_DATA_DIR = $testRoot
try {
    $netdirectorProcess = Start-Process -FilePath $Executable -ArgumentList '--smoke-test' -PassThru -WindowStyle Hidden
    $processHandle = $netdirectorProcess.Handle
    if (-not $netdirectorProcess.WaitForExit(45000)) {
        # Only terminate the specific test process created by this script.
        if ($netdirectorProcess.Path -eq $Executable) { Stop-Process -Id $netdirectorProcess.Id }
        throw 'Packaged app did not exit within 45 seconds.'
    }
    if ($netdirectorProcess.ExitCode -ne 0) { throw "Packaged app exited with $($netdirectorProcess.ExitCode)." }
    $logPath = Join-Path $testRoot 'logs\netdirector.log'
    if (-not (Test-Path -LiteralPath $logPath)) { throw 'Packaged app did not create its runtime log.' }
    $log = Get-Content -LiteralPath $logPath -Raw
    if ($log -notmatch 'Adapter discovery complete' -or $log -match 'WARNING|ERROR') {
        throw "Packaged discovery was not successful. Inspect $logPath"
    }
    Write-Output $log
    Write-Output "PASS: package exited 0 and discovered real adapters. Evidence: $logPath"
} finally {
    $env:NETDIRECTOR_DATA_DIR = $previousDataRoot
}
