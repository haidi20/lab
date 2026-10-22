@echo off
setlocal
set "LOG=%LOCALAPPDATA%\hermes\logs\agent.log"

if not exist "%LOG%" (
    echo Log Hermes tidak ditemukan: %LOG%
    pause
    exit /b 1
)

echo Monitoring Hermes log:
echo %LOG%
echo Tekan Ctrl+C untuk berhenti.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Content -LiteralPath ($env:LOCALAPPDATA + '\hermes\logs\agent.log') -Tail 200 -Wait | Select-String -Pattern 'API call','tool_executor','mcp__trello_lite','cron.scheduler','Turn ended','patch completed','terminal completed','write_file completed','read_file completed','delegate_task','gateway_other_session','No active credentials'"
