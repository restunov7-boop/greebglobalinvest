Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "$PSScriptRoot\_globalgreeninvest_demo_env.ps1"

function Require-Path {
    param(
        [string]$Path,
        [string]$Message
    )
    if (-not (Test-Path $Path)) {
        throw $Message
    }
}

Require-Path $GlobalGreenInvestPython "Backend virtual environment was not found. Create it with: cd backend; py -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt"

Push-Location $GlobalGreenInvestBackendDir
try {
    Write-Host "[1/3] Running migrations" -ForegroundColor Cyan
    & $GlobalGreenInvestPython -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "Migrations failed."
    }

    Write-Host "[2/3] Running GlobalGreenInvest demo seed" -ForegroundColor Cyan
    & $GlobalGreenInvestPython scripts\seed_globalgreeninvest_demo.py
    if ($LASTEXITCODE -ne 0) {
        throw "Demo seed failed."
    }

    Write-Host "[3/3] Running demo diagnostic" -ForegroundColor Cyan
    & $GlobalGreenInvestPython scripts\check_globalgreeninvest_demo.py
    if ($LASTEXITCODE -ne 0) {
        throw "Demo diagnostic failed."
    }
}
finally {
    Pop-Location
}
