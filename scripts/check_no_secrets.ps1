Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RelativeFiles = @(
    ".env.example",
    ".env.cloud.example",
    "README.md",
    "render.yaml",
    "docs\cloud_deployment_runbook.md",
    "docs\render_backend_setup.md",
    "docs\vercel_frontend_setup.md",
    "docs\globalgreeninvest_demo_runbook.md",
    "docs\globalgreeninvest_primary_test_checklist.md"
)

$Warnings = @()

foreach ($Relative in $RelativeFiles) {
    $Path = Join-Path $RepoRoot $Relative
    if (-not (Test-Path $Path)) { continue }
    $Lines = Get-Content -LiteralPath $Path
    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        $Line = $Lines[$Index]
        $LineNumber = $Index + 1

        if (
            $Line -match 'TELEGRAM_BOT_TOKEN\s*=\s*["'']?[^"''\s#]+' -and
            $Line -notmatch 'TELEGRAM_BOT_TOKEN\s*=\s*["'']?($|<|\.\.\.|YOUR_|change_me)'
        ) {
            $Warnings += "$Relative`:$LineNumber TELEGRAM_BOT_TOKEN appears non-placeholder"
        }
        if ($Line -match 'DATABASE_URL\s*=\s*["'']?postgresql\+psycopg://[^:]+:(?!PASSWORD|<PASSWORD>|YOUR_|change_me|postgres@)[^@]+@') {
            $Warnings += "$Relative`:$LineNumber DATABASE_URL appears to contain a real password"
        }
        if (
            $Line -match 'JWT_SECRET\s*=\s*["'']?[^"''\s#]+' -and
            $Line -notmatch 'JWT_SECRET\s*=\s*["'']?($|<|\.\.\.|YOUR_|change_me|change_me_to_long_random_secret)'
        ) {
            $Warnings += "$Relative`:$LineNumber JWT_SECRET appears non-placeholder"
        }
    }
}

if ($Warnings.Count -gt 0) {
    foreach ($Warning in $Warnings) {
        Write-Warning $Warning
    }
    exit 1
}

Write-Host "[OK] No obvious secrets found in deploy docs/templates."
