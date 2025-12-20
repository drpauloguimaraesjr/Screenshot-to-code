Param(
    [string]$AllowOrigins = "",
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000
)

Write-Host "Starting local setup..." -ForegroundColor Cyan

$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $repo

# Ensure Python 3.11 venv exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python venv..." -ForegroundColor Yellow
    py -3.11 -m venv .venv
}

# Upgrade pip
Write-Host "Upgrading pip and installing deps..." -ForegroundColor Yellow
& ".venv/Scripts/python.exe" -m pip install --upgrade pip

# Install backend deps
& ".venv/Scripts/python.exe" -m pip install -r "backend/requirements.txt"
# Install root deps (if any)
if (Test-Path "requirements.txt") {
    & ".venv/Scripts/python.exe" -m pip install -r "requirements.txt"
}

# Set environment variables (CORS, host, port)
if ($AllowOrigins -and $AllowOrigins.Length -gt 0) { $env:ALLOW_ORIGINS = $AllowOrigins }
$env:HOST = $Host
$env:PORT = "$Port"

Write-Host "Starting backend on http://$Host:$Port ..." -ForegroundColor Green
& ".venv/Scripts/python.exe" -m uvicorn backend.app.main:app --host $Host --port $Port

Pop-Location
