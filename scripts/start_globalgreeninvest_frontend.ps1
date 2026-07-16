Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "$PSScriptRoot\_globalgreeninvest_demo_env.ps1"

if (-not (Test-Path $GlobalGreenInvestFrontendDir)) {
    throw "Frontend folder was not found: $GlobalGreenInvestFrontendDir"
}

if ($null -eq (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    throw "pnpm was not found. Install pnpm or make sure it is available in PATH."
}

Write-Host "Starting GlobalGreenInvest frontend:" -ForegroundColor Green
Write-Host "VITE_API_BASE_URL=$env:VITE_API_BASE_URL"
Write-Host "VITE_PROJECT_SLUG=$env:VITE_PROJECT_SLUG"

Push-Location $GlobalGreenInvestFrontendDir
try {
    pnpm dev -- --host 127.0.0.1 --port 5173
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend server exited with code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
