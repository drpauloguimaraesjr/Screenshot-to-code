Param(
    [string]$Output = "Screenshot-to-code.zip"
)

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $repo

$excludeDirs = @(
    ".git",
    ".venv"
)
$excludePatterns = @(
    "*.log",
    "*.tmp"
)

Write-Host "Creating archive: $Output" -ForegroundColor Cyan

# Build file list excluding directories and patterns
$files = Get-ChildItem -Recurse -File | Where-Object {
    $rel = $_.FullName.Substring($repo.Length + 1)
    foreach ($d in $excludeDirs) {
        if ($rel.StartsWith($d)) { return $false }
    }
    foreach ($p in $excludePatterns) {
        if ($rel -like $p) { return $false }
    }
    if ($rel -like "*/__pycache__/*" -or $rel -like "*/.ipynb_checkpoints/*") { return $false }
    return $true
}

$tempZip = Join-Path $env:TEMP ("stc_" + [guid]::NewGuid().ToString() + ".zip")
if (Test-Path $tempZip) { Remove-Item $tempZip -Force }

Add-Type -AssemblyName System.IO.Compression.FileSystem
$fs = [System.IO.File]::Open($tempZip, [System.IO.FileMode]::Create)
$zip = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)

foreach ($f in $files) {
    $rel = $f.FullName.Substring($repo.Length + 1)
    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $f.FullName, $rel, [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
}

$zip.Dispose()
$fs.Dispose()

Move-Item $tempZip $Output -Force
Write-Host "Archive ready: $Output" -ForegroundColor Green
Pop-Location
