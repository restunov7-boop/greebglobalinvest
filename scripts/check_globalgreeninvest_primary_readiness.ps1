param(
    [switch]$ApplyMigrations,
    [switch]$Seed,
    [switch]$CheckBotToken,
    [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"
$Python = Join-Path $BackendDir ".venv\Scripts\python.exe"
$NodeModules = Join-Path $FrontendDir "node_modules"
$FrontendEnvLocal = Join-Path $FrontendDir ".env.local"

function Mask-DatabaseUrl {
    param([string]$Value)
    if (-not $Value) { return "<missing>" }
    return ($Value -replace "://([^:/@]+):([^@]+)@", '://$1:***@')
}

function Read-FrontendEnvValue {
    param([string]$Name)
    if (-not (Test-Path $FrontendEnvLocal)) { return $null }
    $Line = Get-Content -LiteralPath $FrontendEnvLocal | Where-Object { $_ -match "^\s*$Name\s*=" } | Select-Object -First 1
    if (-not $Line) { return $null }
    return (($Line -split "=", 2)[1]).Trim()
}

function Print-State {
    param([string]$State, [string]$Message)
    Write-Host "[$State] $Message"
}

Print-State "INFO" "Repo: $RepoRoot"

if (Test-Path $Python) { Print-State "READY" "Backend venv Python exists." } else { Print-State "BLOCKED" "Backend venv Python is missing." }
if (Test-Path $NodeModules) { Print-State "READY" "Frontend node_modules exists." } else { Print-State "WARNING" "Frontend node_modules is missing." }

$DatabaseUrl = $env:DATABASE_URL
Print-State "INFO" "DATABASE_URL=$(Mask-DatabaseUrl -Value $DatabaseUrl)"

if ($DatabaseUrl) {
    & (Join-Path $PSScriptRoot "check_globalgreeninvest_database.ps1") -ApplyMigrations:$ApplyMigrations
} else {
    Print-State "WARNING" "DATABASE_URL is not set in current shell. DB check may use .env if present."
    & (Join-Path $PSScriptRoot "check_globalgreeninvest_database.ps1") -ApplyMigrations:$ApplyMigrations
}

if ($Seed) {
    if ($Yes) {
        & (Join-Path $PSScriptRoot "prepare_globalgreeninvest_primary_test.ps1") -Yes
    } else {
        & (Join-Path $PSScriptRoot "prepare_globalgreeninvest_primary_test.ps1")
    }
} else {
    Print-State "INFO" "Seed skipped. Use -Seed to run migrations + seed + GlobalGreenInvest diagnostic."
}

& (Join-Path $PSScriptRoot "check_globalgreeninvest_telegram.ps1")

if ($CheckBotToken) {
    & (Join-Path $PSScriptRoot "check_telegram_bot_token.ps1")
} else {
    Print-State "INFO" "Telegram getMe skipped. Use -CheckBotToken when TELEGRAM_BOT_TOKEN is set."
}

$ProjectSlug = Read-FrontendEnvValue -Name "VITE_PROJECT_SLUG"
$ApiBase = Read-FrontendEnvValue -Name "VITE_API_BASE_URL"
$Mock = Read-FrontendEnvValue -Name "VITE_DEV_TELEGRAM_MOCK"

if ($ProjectSlug) { Print-State "INFO" "frontend .env.local VITE_PROJECT_SLUG=$ProjectSlug" } else { Print-State "WARNING" "frontend .env.local has no VITE_PROJECT_SLUG." }
if ($ApiBase) { Print-State "INFO" "frontend .env.local VITE_API_BASE_URL=$ApiBase" } else { Print-State "WARNING" "frontend .env.local has no VITE_API_BASE_URL." }
if ($Mock) { Print-State "INFO" "frontend .env.local VITE_DEV_TELEGRAM_MOCK=$Mock" } else { Print-State "WARNING" "frontend .env.local has no VITE_DEV_TELEGRAM_MOCK." }

Print-State "READY" "Primary readiness check completed. Review warnings before real DB or bot pilot testing."
