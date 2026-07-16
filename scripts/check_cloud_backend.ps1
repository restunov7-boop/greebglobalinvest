param(
    [Parameter(Mandatory = $true)]
    [string]$BackendBaseUrl
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Base = $BackendBaseUrl.TrimEnd("/")
$Checks = @(
    @{ Name = "health"; Url = "$Base/api/v1/health" },
    @{ Name = "community-info"; Url = "$Base/api/v1/community/info" }
)

foreach ($Check in $Checks) {
    try {
        $Response = Invoke-RestMethod -Method Get -Uri $Check.Url -TimeoutSec 20
        Write-Host "[OK] $($Check.Name) $($Check.Url)"
        if ($Response.data) {
            $Response.data | ConvertTo-Json -Depth 4
        }
    } catch {
        Write-Warning "[FAIL] $($Check.Name) $($Check.Url)"
        Write-Warning $_.Exception.Message
        exit 1
    }
}
