Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Test-RequiredPath {
    param([string]$RelativePath, [string]$Label)
    $Path = Join-Path $RepoRoot $RelativePath
    if (Test-Path $Path) {
        Write-Host "[READY] $Label`: $RelativePath"
        return $true
    }
    Write-Warning "[MISSING] $Label`: $RelativePath"
    return $false
}

$Ok = $true
$Ok = (Test-RequiredPath "backend\requirements.txt" "Backend requirements") -and $Ok
$Ok = (Test-RequiredPath "backend\app\main.py" "Backend app entrypoint") -and $Ok
$Ok = (Test-RequiredPath "backend\alembic.ini" "Alembic config") -and $Ok
$Ok = (Test-RequiredPath "backend\alembic\versions" "Alembic migrations") -and $Ok
$Ok = (Test-RequiredPath "frontend\package.json" "Frontend package") -and $Ok
$Ok = (Test-RequiredPath "frontend\vercel.json" "Vercel SPA config") -and $Ok
$Ok = (Test-RequiredPath "render.yaml" "Render blueprint") -and $Ok
$Ok = (Test-RequiredPath ".env.cloud.example" "Cloud env template") -and $Ok
$Ok = (Test-RequiredPath "docs\cloud_deployment_runbook.md" "Cloud deployment runbook") -and $Ok
$Ok = (Test-RequiredPath "docs\render_backend_setup.md" "Render backend docs") -and $Ok
$Ok = (Test-RequiredPath "docs\vercel_frontend_setup.md" "Vercel frontend docs") -and $Ok

$FrontendPackage = Join-Path $RepoRoot "frontend\package.json"
if (Test-Path $FrontendPackage) {
    $Package = Get-Content -LiteralPath $FrontendPackage -Raw | ConvertFrom-Json
    if ($Package.scripts.build) {
        Write-Host "[READY] Frontend build script: $($Package.scripts.build)"
    } else {
        Write-Warning "[MISSING] Frontend build script"
        $Ok = $false
    }
}

$BackendMain = Join-Path $RepoRoot "backend"
$Python = Join-Path $BackendMain ".venv\Scripts\python.exe"
if (Test-Path $Python) {
    Push-Location $BackendMain
    try {
        & $Python -c "import app.main; print('backend_import=ok')"
        if ($LASTEXITCODE -ne 0) { $Ok = $false }
    } finally {
        Pop-Location
    }
} else {
    Write-Warning "[WARNING] Backend venv Python not found locally; Render will create its own environment."
}

& (Join-Path $PSScriptRoot "check_no_secrets.ps1")
if ($LASTEXITCODE -ne 0) {
    $Ok = $false
}

if ($Ok) {
    Write-Host "[READY] Cloud deploy package looks ready."
} else {
    Write-Warning "[BLOCKED] Cloud deploy package has missing or unsafe items."
    exit 1
}
