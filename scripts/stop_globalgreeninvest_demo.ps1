param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Ports = @(8000, 5173)
$Targets = @()

foreach ($Port in $Ports) {
    $Connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($Connection in $Connections) {
        $Process = Get-Process -Id $Connection.OwningProcess -ErrorAction SilentlyContinue
        if ($null -ne $Process) {
            $Targets += [PSCustomObject]@{
                Port = $Port
                Id = $Process.Id
                ProcessName = $Process.ProcessName
                Path = $Process.Path
            }
        }
    }
}

$Targets = @($Targets | Sort-Object Id -Unique)

if ($Targets.Count -eq 0) {
    Write-Host "No listening processes found on ports 8000 or 5173."
    return
}

Write-Host "Processes listening on demo ports:" -ForegroundColor Cyan
$Targets | Format-Table -AutoSize

if (-not $Force) {
    $Answer = Read-Host "Stop these processes? Type YES to continue"
    if ($Answer -ne "YES") {
        Write-Host "Nothing stopped."
        return
    }
}

foreach ($Target in $Targets) {
    if ($Force) {
        Stop-Process -Id $Target.Id -Force
    }
    else {
        Stop-Process -Id $Target.Id
    }
    Write-Host "Stopped process $($Target.Id) on port $($Target.Port)."
}
