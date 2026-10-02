#!/usr/bin/env bash
# Generate all secrets for AERIS deployment.
# Writes to ./secrets/ directory (git-ignored, mode 600).
set -euo pipefail

SECRETS_DIR="$(cd "$(dirname "$0")/.." && pwd)/secrets"
mkdir -p "$SECRETS_DIR"

echo "[*] Generating AERIS secrets into $SECRETS_DIR ..."

# Database passwords
openssl rand -base64 32 | tr -d '\n' > "$SECRETS_DIR/db_admin_password"
openssl rand -base64 32 | tr -d '\n' > "$SECRETS_DIR/db_password"
openssl rand -base64 32 | tr -d '\n' > "$SECRETS_DIR/db_migrator_password"

# JWT signing key (256-bit)
openssl rand -base64 48 | tr -d '\n' > "$SECRETS_DIR/jwt_signing_key"

# AES-256 field-encryption key (32 bytes hex + key ID)
AES_KEY=$(openssl rand -hex 32)
echo "{\"key_id\": \"k1\", \"key\": \"$AES_KEY\"}" > "$SECRETS_DIR/aes_encryption_key"

# Ed25519 keypair for Evidence Passport signing
openssl genpkey -algorithm Ed25519 -out "$SECRETS_DIR/ed25519_private_key" 2>/dev/null
openssl pkey -in "$SECRETS_DIR/ed25519_private_key" -pubout -out "$SECRETS_DIR/ed25519_public_key" 2>/dev/null

# Model HMAC key
openssl rand -base64 32 | tr -d '\n' > "$SECRETS_DIR/model_hmac_key"

# Demo user passwords
DEMO_PASS_SUPERVISOR=$(openssl rand -base64 16 | tr -d '\n/+=')
DEMO_PASS_PLANNER=$(openssl rand -base64 16 | tr -d '\n/+=')
DEMO_PASS_ENGINEER=$(openssl rand -base64 16 | tr -d '\n/+=')
DEMO_PASS_SPARES=$(openssl rand -base64 16 | tr -d '\n/+=')
DEMO_PASS_ADMIN=$(openssl rand -base64 16 | tr -d '\n/+=')

cat > "$SECRETS_DIR/demo_credentials.txt" << EOF
=== AERIS Demo Credentials ===
Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
WARNING: These are for demonstration only. Change before any deployment.

Username              | Role               | Password
----------------------|--------------------|--------------------------
fleet_supervisor      | FLEET_SUPERVISOR   | ${DEMO_PASS_SUPERVISOR}
maint_planner         | MAINT_PLANNER      | ${DEMO_PASS_PLANNER}
maint_engineer        | MAINT_ENGINEER     | ${DEMO_PASS_ENGINEER}
spares_planner        | SPARES_PLANNER     | ${DEMO_PASS_SPARES}
sys_admin             | SYS_ADMIN          | ${DEMO_PASS_ADMIN}
EOF

# Set restrictive permissions
chmod 600 "$SECRETS_DIR"/*

echo "[+] All secrets generated successfully."
echo "[+] Demo credentials written to $SECRETS_DIR/demo_credentials.txt"
