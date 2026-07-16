Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "$PSScriptRoot\_globalgreeninvest_demo_env.ps1"

$DiagnosticScript = Join-Path $GlobalGreenInvestBackendDir "scripts\check_globalgreeninvest_demo.py"

if (-not (Test-Path $GlobalGreenInvestPython)) {
    throw "Backend virtual environment was not found. Create it with: cd backend; py -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt"
}

if (-not (Test-Path $DiagnosticScript)) {
    throw "Diagnostic script was not found: $DiagnosticScript"
}

Push-Location $GlobalGreenInvestBackendDir
try {
    & $GlobalGreenInvestPython $DiagnosticScript
    if ($LASTEXITCODE -ne 0) {
        throw "Demo diagnostic failed."
    }
}
finally {
    Pop-Location
}
