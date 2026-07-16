param(
    [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BackendDir = Join-Path $RepoRoot "backend"
$Python = Join-Path $BackendDir ".venv\Scripts\python.exe"

function Get-EnvFileValue {
    param([string]$Name)
    $EnvFile = Join-Path $RepoRoot ".env"
    if (-not (Test-Path $EnvFile)) { return $null }
    $Line = Get-Content -LiteralPath $EnvFile | Where-Object { $_ -match "^\s*$Name\s*=" } | Select-Object -First 1
    if (-not $Line) { return $null }
    return (($Line -split "=", 2)[1]).Trim()
}

function Mask-DatabaseUrl {
    param([string]$Value)
    if (-not $Value) { return "<missing>" }
    return ($Value -replace "://([^:/@]+):([^@]+)@", '://$1:***@')
}

function Is-SqliteUrl {
    param([string]$Value)
    return $Value.StartsWith("sqlite", [System.StringComparison]::OrdinalIgnoreCase)
}

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment was not found: $Python"
}

$DatabaseUrl = $env:DATABASE_URL
if (-not $DatabaseUrl) {
    $DatabaseUrl = Get-EnvFileValue -Name "DATABASE_URL"
    if ($DatabaseUrl) {
        $env:DATABASE_URL = $DatabaseUrl
        Write-Host "[INFO] DATABASE_URL loaded from .env for this run."
    }
}

if (-not $DatabaseUrl) {
    throw "DATABASE_URL is not configured. Set it before preparing primary test data."
}

Write-Host "DATABASE_URL_MASKED=$(Mask-DatabaseUrl -Value $DatabaseUrl)"

if (-not (Is-SqliteUrl -Value $DatabaseUrl) -and -not $Yes) {
    Write-Host "This will run migrations and seed GlobalGreenInvest on the configured external database."
    $Answer = Read-Host "Continue? Type YES"
    if ($Answer -ne "YES") {
        Write-Host "Cancelled."
        exit 1
    }
}

Push-Location $BackendDir
try {
    Write-Host "[1/3] Running migrations"
    & $Python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw "Alembic migration failed." }

    Write-Host "[2/3] Running GlobalGreenInvest seed"
    & $Python "scripts\seed_globalgreeninvest_demo.py"
    if ($LASTEXITCODE -ne 0) { throw "GlobalGreenInvest seed failed." }

    Write-Host "[3/3] Running GlobalGreenInvest diagnostic"
    & $Python "scripts\check_globalgreeninvest_demo.py"
    if ($LASTEXITCODE -ne 0) { throw "GlobalGreenInvest diagnostic failed." }
}
finally {
    Pop-Location
}
