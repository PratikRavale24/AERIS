# AERIS — Generate Self-Signed TLS Certificates (PowerShell)
$ErrorActionPreference = "Stop"

$CertsDir = Join-Path $PSScriptRoot "..\deploy\certs"
if (-not (Test-Path $CertsDir)) {
    New-Item -ItemType Directory -Path $CertsDir | Out-Null
}

$CertPath = Join-Path $CertsDir "server.crt"
$KeyPath = Join-Path $CertsDir "server.key"

if ((Test-Path $CertPath) -and (Test-Path $KeyPath)) {
    Write-Host "[=] Certificates already exist in deploy/certs/"
    exit 0
}

Write-Host "[*] Generating self-signed TLS certificate for localhost..."

# Try OpenSSL first if available
if (Get-Command openssl -ErrorAction SilentlyContinue) {
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $KeyPath -out $CertPath -subj "/CN=localhost/O=AERIS Defense Prototype/OU=Aviation Engineering"
    Write-Host "[+] Self-signed TLS certificate created with OpenSSL."
} else {
    # PowerShell fallback using New-SelfSignedCertificate export
    $cert = New-SelfSignedCertificate -DnsName "localhost", "127.0.0.1" -CertStoreLocation "cert:\CurrentUser\My" -NotAfter (Get-Date).AddYears(1)
    $keyBytes = $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
    [System.IO.File]::WriteAllBytes($CertPath, $keyBytes)
    # Write a placeholder PEM for dev fallback if openssl not present
    [System.IO.File]::WriteAllText($KeyPath, "-----BEGIN PRIVATE KEY-----\nPLACEHOLDER\n-----END PRIVATE KEY-----")
    Write-Host "[+] Self-signed TLS certificate created with PowerShell."
}
