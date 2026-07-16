param(
    [switch]$OpenBrowser,
    [switch]$UseDockerDb
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "$PSScriptRoot\_globalgreeninvest_demo_env.ps1"

function Write-Stage {
    param([string]$Message)
    Write-Host ""
    Write-Host $Message -ForegroundColor Cyan
}

function Require-Path {
    param(
        [string]$Path,
        [string]$Message
    )
    if (-not (Test-Path $Path)) {
        throw $Message
    }
}

function Invoke-BackendPython {
    param(
        [string]$BackendDir,
        [string]$Python,
        [string[]]$PythonArgs
    )

    Push-Location $BackendDir
    try {
        & $Python @PythonArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Backend command failed: $Python $($PythonArgs -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

function Start-DatabaseIfAvailable {
    param(
        [string]$RepoRoot,
        [string]$DockerComposeFile
    )

    $Docker = Get-Command docker -ErrorAction SilentlyContinue
    if ($null -eq $Docker) {
        Write-Warning "Docker not found. Skipping DB startup. Make sure your database is already running."
        return
    }

    Push-Location $RepoRoot
    try {
        Write-Host "Trying: docker compose up -d db"
        & $Docker.Source compose up -d db
        if ($LASTEXITCODE -eq 0) {
            return
        }

        Write-Warning "Docker compose service 'db' did not start. Checking compose services."
        $services = & $Docker.Source compose -f $DockerComposeFile config --services 2>$null
        if ($LASTEXITCODE -eq 0 -and ($services -contains "postgres")) {
            Write-Host "Trying: docker compose up -d postgres"
            & $Docker.Source compose -f $DockerComposeFile up -d postgres
            if ($LASTEXITCODE -eq 0) {
                return
            }
        }

        Write-Host "Trying fallback: docker compose up -d"
        & $Docker.Source compose -f $DockerComposeFile up -d
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Docker compose startup failed. Continuing; migrations will fail if the database is unavailable."
        }
    }
    finally {
        Pop-Location
    }
}

function Wait-ForUrl {
    param(
        [string]$Name,
        [string]$Url,
        [int]$Attempts = 20
    )

    for ($Index = 1; $Index -le $Attempts; $Index++) {
        try {
            $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 500) {
                Write-Host "$Name is responding: $Url" -ForegroundColor Green
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }

    Write-Warning "$Name did not respond at $Url within the wait window. Check the server PowerShell window for details."
    return $false
}

$RepoRoot = $GlobalGreenInvestRepoRoot
$BackendDir = $GlobalGreenInvestBackendDir
$FrontendDir = $GlobalGreenInvestFrontendDir
$ScriptsDir = Join-Path $RepoRoot "scripts"
$Python = $GlobalGreenInvestPython
$DockerComposeFile = Join-Path $RepoRoot "docker-compose.yml"
$BackendStartScript = Join-Path $ScriptsDir "start_globalgreeninvest_backend_sqlite.ps1"
$FrontendStartScript = Join-Path $ScriptsDir "start_globalgreeninvest_frontend.ps1"

Write-Host "GlobalGreenInvest demo launcher" -ForegroundColor Green
Write-Host "Repo: $RepoRoot"
Write-Host "Mode: local SQLite demo DB"
Write-Host "DATABASE_URL=$env:DATABASE_URL"

Write-Stage "[1/7] Checking prerequisites"
Require-Path $Python "Backend virtual environment was not found. Create it with: cd backend; py -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt"
Require-Path $FrontendDir "Frontend folder was not found: $FrontendDir"
Require-Path $DockerComposeFile "docker-compose.yml was not found: $DockerComposeFile"
Require-Path $BackendStartScript "Backend dev script was not found: $BackendStartScript"
Require-Path $FrontendStartScript "Frontend dev script was not found: $FrontendStartScript"
if ($null -eq (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    throw "pnpm was not found. Install pnpm or make sure it is available in PATH."
}
if ($null -eq (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Warning "Docker not found. Using local SQLite demo mode."
}
Write-Host "Prerequisites look good."

Write-Stage "[2/7] Starting database"
if ($UseDockerDb) {
    Write-Warning "-UseDockerDb was requested, but this launcher still runs the demo against local SQLite unless backend env vars are changed explicitly."
    Start-DatabaseIfAvailable -RepoRoot $RepoRoot -DockerComposeFile $DockerComposeFile
}
else {
    Write-Host "Using local SQLite demo database. Docker/Postgres startup skipped."
}

Write-Stage "[3/7] Running migrations"
Invoke-BackendPython -BackendDir $BackendDir -Python $Python -PythonArgs @("-m", "alembic", "upgrade", "head")

Write-Stage "[4/7] Running GlobalGreenInvest demo seed"
Invoke-BackendPython -BackendDir $BackendDir -Python $Python -PythonArgs @("scripts\seed_globalgreeninvest_demo.py")

Write-Stage "[5/7] Running demo diagnostic"
Invoke-BackendPython -BackendDir $BackendDir -Python $Python -PythonArgs @("scripts\check_globalgreeninvest_demo.py")

Write-Stage "[6/7] Starting backend"
Start-Process -FilePath "powershell.exe" -WorkingDirectory $RepoRoot -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $BackendStartScript
)
Write-Host "Backend dev server is starting in a new PowerShell window."

Write-Stage "[7/7] Starting frontend"
Start-Process -FilePath "powershell.exe" -WorkingDirectory $RepoRoot -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $FrontendStartScript
)
Write-Host "Frontend dev server is starting in a new PowerShell window."

Write-Host ""
Write-Host "Waiting briefly for local servers..." -ForegroundColor Cyan
[void](Wait-ForUrl -Name "Backend" -Url "http://127.0.0.1:8000/api/v1/community/public-links" -Attempts 20)
[void](Wait-ForUrl -Name "Frontend" -Url "http://127.0.0.1:5173/app" -Attempts 20)

Write-Host ""
Write-Host "Demo URLs" -ForegroundColor Green
Write-Host "Backend:        http://127.0.0.1:8000"
Write-Host "Frontend:       http://127.0.0.1:5173"
Write-Host "Demo:           http://127.0.0.1:5173/app"
Write-Host "Products:       http://127.0.0.1:5173/app/products"
Write-Host "Admin products: http://127.0.0.1:5173/admin/products"
Write-Host "Admin posts:    http://127.0.0.1:5173/admin/posts"
Write-Host "Admin insights: http://127.0.0.1:5173/admin/insights"

if ($OpenBrowser) {
    Start-Process "http://127.0.0.1:5173/app"
}
