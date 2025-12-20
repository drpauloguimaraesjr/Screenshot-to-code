Param(
    [string]$Output = "Screenshot-to-code.zip"
)

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $repo

$exclude = @(
    ".git",
    ".venv",
    "**/.ipynb_checkpoints",
    "**/__pycache__",
    "**/*.log"
)

Write-Host "Creating archive: $Output" -ForegroundColor Cyan

# Build file list excluding patterns
$files = Get-ChildItem -Recurse -File | Where-Object {
    $path = $_.FullName.Replace($repo + "\", "")
    foreach ($pattern in $exclude) {
        if ($path -like $pattern) { return $false }
    }
    return $true
}

# Create zip in temp folder then move
$tempZip = Join-Path $env:TEMP ("stc_" + [guid]::NewGuid().ToString() + ".zip")
if (Test-Path $tempZip) { Remove-Item $tempZip -Force }

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($repo, $tempZip)
Move-Item $tempZip $Output -Force

Write-Host "Archive ready: $Output" -ForegroundColor Green
Pop-Location
