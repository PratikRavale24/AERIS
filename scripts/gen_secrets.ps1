# AERIS — Generate Secrets (PowerShell)
$ErrorActionPreference = "Stop"

$SecretsDir = Join-Path $PSScriptRoot "..\secrets"
if (-not (Test-Path $SecretsDir)) {
    New-Item -ItemType Directory -Path $SecretsDir | Out-Null
}

function Generate-RandomString($length=32) {
    $bytes = New-Object byte[] $length
    (New-Object Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
    return [Convert]::ToBase64String($bytes).Replace('+', '').Replace('/', '').Replace('=', '').Substring(0, $length)
}

function Write-SecretFile($filename, $content) {
    $path = Join-Path $SecretsDir $filename
    if (-not (Test-Path $path)) {
        [System.IO.File]::WriteAllText($path, $content)
        Write-Host "[+] Generated secret: $filename"
    } else {
        Write-Host "[=] Secret exists: $filename"
    }
}

Write-SecretFile "db_admin_password" (Generate-RandomString 32)
Write-SecretFile "db_password" (Generate-RandomString 32)
Write-SecretFile "db_migrator_password" (Generate-RandomString 32)
Write-SecretFile "jwt_signing_key" (Generate-RandomString 64)
Write-SecretFile "aes_encryption_key" (Generate-RandomString 32)
Write-SecretFile "model_hmac_key" (Generate-RandomString 64)

# Generate Ed25519 dummy keypair files if missing
Write-SecretFile "ed25519_private_key" "-----BEGIN PRIVATE KEY-----`nMIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQg$(Generate-RandomString 32)`n-----END PRIVATE KEY-----"
Write-SecretFile "ed25519_public_key" "-----BEGIN PUBLIC KEY-----`nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE$(Generate-RandomString 44)`n-----END PUBLIC KEY-----"

# Create demo credentials summary
$DemoCreds = @"
===================================================================
 AERIS DEMO CREDENTIALS — SYNTHETIC / DEMO ENVIRONMENT
===================================================================

ROLE                    USERNAME        DEFAULT PASSWORD
-------------------------------------------------------------------
Air Base Commander      commander1      CommanderPass123!
Maintenance Supervisor  supervisor1     SupervisorPass123!
Flight Test Engineer    engineer1       EngineerPass123!
Supply Chain Officer    logistics1      LogisticsPass123!
Security Auditor        auditor1        AuditorPass123!
System Admin            admin1          AdminPass123!

===================================================================
"@

$DemoPath = Join-Path $SecretsDir "demo_credentials.txt"
[System.IO.File]::WriteAllText($DemoPath, $DemoCreds)
Write-Host "[+] Demo credentials written to secrets/demo_credentials.txt"
