#Requires -Version 5.1
<#
    Останавливает только те процессы, которые поднял run-all.ps1:
    PID берутся из logs/pids.json, чужие процессы не затрагиваются.
#>

$root = $PSScriptRoot
$manifest = Join-Path $root "logs\pids.json"

if (-not (Test-Path -LiteralPath $manifest)) {
    Write-Host "Нет logs/pids.json — похоже, run-all.ps1 ещё не запускался." -ForegroundColor Yellow
    exit 0
}

$services = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json

foreach ($service in $services) {
    $process = Get-Process -Id $service.pid -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $service.pid -Force
        Write-Host ("остановлен {0} (pid {1})" -f $service.name, $service.pid)
    } else {
        Write-Host ("{0} уже не работает" -f $service.name) -ForegroundColor DarkGray
    }
}

Remove-Item -LiteralPath $manifest -Force
