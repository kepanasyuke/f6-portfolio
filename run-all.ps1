#Requires -Version 5.1
<#
    Поднимает портфолио-сайт и все семь сервисов стенда.
    Каждый процесс запускается скрыто, PID пишутся в logs/pids.json,
    логи — в logs/<имя>.out.log и logs/<имя>.err.log.
#>

$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$logs = Join-Path $root "logs"

if (-not (Test-Path -LiteralPath $python)) {
    Write-Host "Не найдено окружение .venv. Создайте его: python -m venv .venv" -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Path $logs -Force | Out-Null

$services = @(
    @{ name = "site"; port = 8100; dir = $root; args = @("-m", "http.server", "8100", "--bind", "127.0.0.1", "--directory", $root) },
    @{ name = "01-feed-harvester"; port = 8101; dir = (Join-Path $root "01-feed-harvester") },
    @{ name = "02-hunt-rules"; port = 8102; dir = (Join-Path $root "02-hunt-rules") },
    @{ name = "03-log-forge"; port = 8103; dir = (Join-Path $root "03-log-forge") },
    @{ name = "04-botnet-map"; port = 8104; dir = (Join-Path $root "04-botnet-map") },
    @{ name = "05-typosquat-radar"; port = 8105; dir = (Join-Path $root "05-typosquat-radar") },
    @{ name = "06-report-builder"; port = 8106; dir = (Join-Path $root "06-report-builder") },
    @{ name = "07-ops-agent"; port = 8107; dir = (Join-Path $root "07-ops-agent") }
)

$started = @()

foreach ($service in $services) {
    $argumentList = if ($service.ContainsKey("args")) {
        $service.args
    } else {
        @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$($service.port)", "--app-dir", $service.dir)
    }

    $process = Start-Process -FilePath $python `
        -ArgumentList $argumentList `
        -WorkingDirectory $service.dir `
        -WindowStyle Hidden `
        -PassThru `
        -RedirectStandardOutput (Join-Path $logs "$($service.name).out.log") `
        -RedirectStandardError (Join-Path $logs "$($service.name).err.log")

    $started += [pscustomobject]@{ name = $service.name; port = $service.port; pid = $process.Id }
    Write-Host ("запущен {0} на порту {1} (pid {2})" -f $service.name, $service.port, $process.Id)
}

$started | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logs "pids.json") -Encoding UTF8

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Портфолио:        http://127.0.0.1:8100/site/" -ForegroundColor Green
foreach ($service in $services | Where-Object { $_.port -ne 8100 }) {
    Write-Host ("{0,-22} http://127.0.0.1:{1}/" -f $service.name, $service.port)
}
Write-Host ""
Write-Host "Документация API: http://127.0.0.1:8101/api/docs (и так далее по портам)"
Write-Host "Остановить:       .\stop-all.ps1"
