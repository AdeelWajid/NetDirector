param(
    [ValidateSet('x86', 'x64')][string]$Architecture = 'x64',
    [string]$Version = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not $Version) {
    $Version = (Get-Content (Join-Path $projectRoot "VERSION") -Raw).Trim()
}

Push-Location $projectRoot
try {
    # 1. Ensure ForceBindIP is fetched and copied into dist
    & python scripts/fetch_forcebindip.py
    if ($LASTEXITCODE -ne 0) { throw 'Failed to fetch ForceBindIP binaries.' }

    $distTarget = Join-Path $projectRoot "dist\$Architecture\NetDirector\ForceBindIP"
    if (Test-Path (Join-Path $projectRoot "dist\$Architecture\NetDirector")) {
        New-Item -ItemType Directory -Path $distTarget -Force | Out-Null
        Copy-Item -Path (Join-Path $projectRoot "build\ForceBindIP\*") -Destination $distTarget -Force
    }

    # 2. Locate Inno Setup Compiler (ISCC)
    $isccCommand = Get-Command iscc -ErrorAction SilentlyContinue
    $isccPath = if ($isccCommand) { $isccCommand.Source } else { $null }

    if (-not $isccPath) {
        $searchPaths = @(
            "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
            "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            "C:\Program Files\Inno Setup 6\ISCC.exe"
        )
        foreach ($candidate in $searchPaths) {
            if (Test-Path $candidate) {
                $isccPath = $candidate
                break
            }
        }
    }

    if (-not $isccPath) {
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            Write-Host "Installing Inno Setup via Chocolatey..."
            choco install innosetup -y --no-progress
            if (Test-Path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe") {
                $isccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
            }
        }
    }

    if (-not $isccPath) {
        Write-Warning "Inno Setup Compiler (ISCC.exe) not found. Skipping installer build."
        return
    }

    Write-Host "Compiling Windows installer with $isccPath..."
    & $isccPath /Qp "/DMyAppVersion=$Version" "/DMyAppArch=$Architecture" scripts/installer.iss
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup compilation failed.' }

    # 3. Generate SHA256 checksum for the installer
    $setupFile = Join-Path $projectRoot "release\NetDirector-$Version-windows-$Architecture-Setup.exe"
    if (Test-Path $setupFile) {
        $hash = (Get-FileHash -Path $setupFile -Algorithm SHA256).Hash.ToLower()
        $checksumContent = "$hash  $([System.IO.Path]::GetFileName($setupFile))`n"
        $checksumFile = [System.IO.Path]::ChangeExtension($setupFile, ".sha256")
        [System.IO.File]::WriteAllText($checksumFile, $checksumContent, [System.Text.Encoding]::ASCII)
        Write-Host "Installer created: $setupFile"
        Write-Host "Checksum created: $checksumFile"
    }
} finally {
    Pop-Location
}
