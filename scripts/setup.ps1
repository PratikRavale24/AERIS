# AERIS — Windows Setup Script (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " AERIS — Setup & Docker Initialization (Windows)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Generate secrets
Write-Host "`n[Step 1/3] Generating Secrets..." -ForegroundColor Yellow
& "$PSScriptRoot\gen_secrets.ps1"

# 2. Generate certificates
Write-Host "`n[Step 2/3] Generating TLS Certificates..." -ForegroundColor Yellow
& "$PSScriptRoot\gen_certs.ps1"

# 3. Build docker images
Write-Host "`n[Step 3/3] Building Docker Containers..." -ForegroundColor Yellow
docker compose build

Write-Host "`n[+] Setup complete! Run .\scripts\up.ps1 to start services." -ForegroundColor Green
