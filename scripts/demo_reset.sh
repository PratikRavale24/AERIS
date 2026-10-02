#!/usr/bin/env bash
# Reset AERIS to clean demo state.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "[*] Resetting AERIS to demo state..."
echo "[1/5] Stopping services..."
docker compose down -v 2>/dev/null || true

echo "[2/5] Regenerating secrets..."
bash scripts/gen_secrets.sh

echo "[3/5] Regenerating certificates..."
bash scripts/gen_certs.sh

echo "[4/5] Starting services..."
docker compose up -d --build

echo "[5/5] Waiting for services and seeding..."
sleep 10
docker compose exec backend python -m app.db.seed

echo "[+] Demo reset complete."
echo "[+] Access: https://localhost:8443"
echo "[+] Credentials: see secrets/demo_credentials.txt"
