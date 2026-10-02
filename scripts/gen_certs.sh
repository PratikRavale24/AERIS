#!/usr/bin/env bash
# Generate self-signed TLS certificates for AERIS nginx.
set -euo pipefail

CERT_DIR="$(cd "$(dirname "$0")/.." && pwd)/deploy/certs"
mkdir -p "$CERT_DIR"

echo "[*] Generating self-signed TLS certificate..."

openssl req -x509 -newkey rsa:4096 \
    -keyout "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.crt" \
    -days 365 \
    -nodes \
    -subj "/CN=aeris-local/O=AERIS Prototype/OU=Development" \
    -addext "subjectAltName=DNS:localhost,DNS:aeris-local,IP:127.0.0.1" \
    2>/dev/null

chmod 600 "$CERT_DIR/server.key"
chmod 644 "$CERT_DIR/server.crt"

echo "[+] Certificate generated:"
echo "    Key:  $CERT_DIR/server.key"
echo "    Cert: $CERT_DIR/server.crt"
echo "[!] This is a self-signed certificate for development/demo use only."
