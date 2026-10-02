# AERIS — Start Services (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "[*] Starting AERIS Docker containers..." -ForegroundColor Cyan
docker compose up -d

Write-Host "[+] AERIS services starting up!" -ForegroundColor Green
Write-Host "[+] Web Application: https://localhost:8443" -ForegroundColor Green
Write-Host "[+] Waiting for healthy status..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
docker compose ps
