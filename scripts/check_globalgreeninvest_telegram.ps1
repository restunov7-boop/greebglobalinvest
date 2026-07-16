param(
    [switch]$ShowIds
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Mode = if ($env:TELEGRAM_SENDER_MODE) { $env:TELEGRAM_SENDER_MODE } else { "mock" }
$Scope = if ($env:TELEGRAM_REAL_SEND_SCOPE) { $env:TELEGRAM_REAL_SEND_SCOPE } else { "pilot" }
$TokenConfigured = -not [string]::IsNullOrWhiteSpace($env:TELEGRAM_BOT_TOKEN)
$PilotChatConfigured = -not [string]::IsNullOrWhiteSpace($env:TELEGRAM_PILOT_CHAT_ID)
$PilotUserConfigured = -not [string]::IsNullOrWhiteSpace($env:TELEGRAM_PILOT_TELEGRAM_USER_ID)

Write-Host "TELEGRAM_SENDER_MODE=$Mode"
Write-Host "TELEGRAM_REAL_SEND_SCOPE=$Scope"
Write-Host "TELEGRAM_BOT_TOKEN_CONFIGURED=$TokenConfigured"
Write-Host "TELEGRAM_PILOT_CHAT_ID_CONFIGURED=$PilotChatConfigured"
Write-Host "TELEGRAM_PILOT_TELEGRAM_USER_ID_CONFIGURED=$PilotUserConfigured"

if ($ShowIds) {
    Write-Host "TELEGRAM_PILOT_CHAT_ID=$($env:TELEGRAM_PILOT_CHAT_ID)"
    Write-Host "TELEGRAM_PILOT_TELEGRAM_USER_ID=$($env:TELEGRAM_PILOT_TELEGRAM_USER_ID)"
}

if ($Mode -eq "mock") {
    Write-Host "SAFETY=READY: mock mode sends no real Telegram messages."
} elseif ($Mode -eq "real" -and $Scope -eq "pilot" -and $TokenConfigured -and ($PilotChatConfigured -or $PilotUserConfigured)) {
    Write-Host "SAFETY=READY: real pilot mode is configured for an explicit target."
} elseif ($Mode -eq "real" -and $Scope -eq "pilot") {
    Write-Warning "SAFETY=BLOCKED: real pilot mode needs a token and pilot target."
} elseif ($Mode -eq "real" -and $Scope -eq "all") {
    Write-Warning "SAFETY=DANGER: real all scope can send to every eligible pending recipient."
} else {
    Write-Warning "SAFETY=WARNING: Telegram sender environment is unusual."
}

try {
    $Status = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/v1/community/admin/notifications/sender-status" -TimeoutSec 5
    Write-Host "BACKEND_SENDER_STATUS=reachable"
    if ($Status.data) {
        Write-Host "BACKEND_MODE=$($Status.data.mode)"
        Write-Host "BACKEND_REAL_ENABLED=$($Status.data.real_enabled)"
        Write-Host "BACKEND_TOKEN_CONFIGURED=$($Status.data.token_configured)"
        Write-Host "BACKEND_SCOPE=$($Status.data.real_send_scope)"
        Write-Host "BACKEND_PILOT_TARGET_CONFIGURED=$($Status.data.pilot_target_configured)"
    }
} catch {
    Write-Warning "Backend sender-status endpoint was not reachable without an admin session. Use /admin/settings for authenticated status."
}
