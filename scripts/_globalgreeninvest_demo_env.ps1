Set-StrictMode -Version Latest

$GlobalGreenInvestRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$GlobalGreenInvestBackendDir = Join-Path $GlobalGreenInvestRepoRoot "backend"
$GlobalGreenInvestFrontendDir = Join-Path $GlobalGreenInvestRepoRoot "frontend"
$GlobalGreenInvestPython = Join-Path $GlobalGreenInvestBackendDir ".venv\Scripts\python.exe"
$GlobalGreenInvestDatabasePath = Join-Path $GlobalGreenInvestBackendDir "local_dev.db"
$GlobalGreenInvestDatabaseUrlPath = ([System.IO.Path]::GetFullPath($GlobalGreenInvestDatabasePath)).Replace("\", "/")

$env:APP_ENV = "development"
$env:DATABASE_URL = "sqlite:///$GlobalGreenInvestDatabaseUrlPath"
$env:DEV_AUTH_ENABLED = "true"
$env:JWT_SECRET = "dev_secret_change_me"
$env:CORS_ORIGINS = "http://127.0.0.1:5173,http://localhost:5173"

$env:VITE_API_BASE_URL = "http://127.0.0.1:8000/api/v1"
$env:VITE_PROJECT_SLUG = "global-green-invest"
$env:VITE_DEV_TELEGRAM_MOCK = "true"
