param(
    [switch]$ApplyMigrations
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

function Get-DatabaseMode {
    param([string]$Value)
    if (-not $Value) { return "missing" }
    if ($Value.StartsWith("sqlite", [System.StringComparison]::OrdinalIgnoreCase)) { return "sqlite" }
    if ($Value.StartsWith("postgres", [System.StringComparison]::OrdinalIgnoreCase)) { return "postgres/external" }
    return "unknown"
}

if (-not (Test-Path $Python)) {
    throw "Backend virtual environment was not found: $Python"
}

$DatabaseUrl = $env:DATABASE_URL
if (-not $DatabaseUrl) {
    $DatabaseUrl = Get-EnvFileValue -Name "DATABASE_URL"
    if ($DatabaseUrl) {
        $env:DATABASE_URL = $DatabaseUrl
        Write-Host "[INFO] DATABASE_URL loaded from .env for this check."
    }
}

$Mode = Get-DatabaseMode -Value $DatabaseUrl
Write-Host "DATABASE_URL_MODE=$Mode"
Write-Host "DATABASE_URL_MASKED=$(Mask-DatabaseUrl -Value $DatabaseUrl)"

if (-not $DatabaseUrl) {
    Write-Warning "DATABASE_URL is not set. Configure it before primary DB testing."
    exit 1
}

Push-Location $BackendDir
try {
    Write-Host "[1/3] Checking DB connection"
    & $Python -c "from app.config import settings; from sqlalchemy import create_engine, text; engine=create_engine(settings.database_url); conn=engine.connect(); print('db_connect=ok'); print(conn.execute(text('select 1')).scalar()); conn.close()"
    if ($LASTEXITCODE -ne 0) { throw "Database connection check failed." }

    Write-Host "[2/3] Checking Alembic revision"
    & $Python -m alembic current
    if ($LASTEXITCODE -ne 0) { throw "Alembic current failed." }
    & $Python -m alembic heads
    if ($LASTEXITCODE -ne 0) { throw "Alembic heads failed." }

    if ($ApplyMigrations) {
        Write-Host "[3/3] Applying migrations"
        & $Python -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw "Alembic upgrade failed." }
    } else {
        Write-Host "[3/3] Migration apply skipped. Use -ApplyMigrations to run alembic upgrade head."
    }
}
finally {
    Pop-Location
}
