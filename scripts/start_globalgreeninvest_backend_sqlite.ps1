Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "$PSScriptRoot\_globalgreeninvest_demo_env.ps1"

if (-not (Test-Path $GlobalGreenInvestPython)) {
    throw "Backend virtual environment was not found. Create it with: cd backend; py -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt"
}

Write-Host "Starting GlobalGreenInvest backend with SQLite demo DB:" -ForegroundColor Green
Write-Host $env:DATABASE_URL

Push-Location $GlobalGreenInvestBackendDir
try {
    & $GlobalGreenInvestPython -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    if ($LASTEXITCODE -ne 0) {
        throw "Backend server exited with code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
