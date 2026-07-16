Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($env:TELEGRAM_BOT_TOKEN)) {
    Write-Warning "TELEGRAM_BOT_TOKEN is not set. Nothing to check."
    exit 1
}

$ApiBaseUrl = if ($env:TELEGRAM_API_BASE_URL) { $env:TELEGRAM_API_BASE_URL.TrimEnd("/") } else { "https://api.telegram.org" }
$Url = "$ApiBaseUrl/bot$($env:TELEGRAM_BOT_TOKEN)/getMe"

Write-Host "Checking Telegram Bot API getMe. Token will not be printed."

try {
    $Response = Invoke-RestMethod -Method Get -Uri $Url -TimeoutSec 10
    if ($Response.ok -and $Response.result) {
        Write-Host "BOT_CHECK=ok"
        Write-Host "BOT_ID=$($Response.result.id)"
        Write-Host "BOT_USERNAME=$($Response.result.username)"
    } else {
        Write-Warning "Telegram getMe returned an unexpected response."
        exit 1
    }
} catch {
    Write-Warning "Telegram getMe failed. Check token, network access, and TELEGRAM_API_BASE_URL."
    exit 1
}
