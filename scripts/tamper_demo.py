"""AERIS — Tamper Demo Script.

Demonstrates evidence passport tamper detection by modifying a health reading
using the privileged admin DB role (outside the app's access).
This is run via `make tamper-demo`.
"""
from __future__ import annotations

import os
import sys

import psycopg2


def main() -> None:
    """Modify a health reading to demonstrate tamper detection."""
    # Use admin credentials (not available to the app)
    db_password = ""
    secret_path = "/run/secrets/db_admin_password"
    if os.path.exists(secret_path):
        with open(secret_path) as f:
            db_password = f.read().strip()
    else:
        db_password = os.environ.get("POSTGRES_PASSWORD", "")

    if not db_password:
        print("[!] Could not read admin DB password. Ensure secrets are mounted.")
        sys.exit(1)

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "aeris"),
        user="aeris_admin",
        password=db_password,
    )

    try:
        cur = conn.cursor()

        # Find a health reading for the hero component A-017-ENG-02
        cur.execute("""
            SELECT id, value, sensor
            FROM health_observations
            WHERE component_id = 'A-017-ENG-02'
            ORDER BY cycle DESC
            LIMIT 1
        """)
        row = cur.fetchone()

        if row is None:
            print("[!] No health observations found for A-017-ENG-02.")
            print("[!] Run 'make seed' first.")
            sys.exit(1)

        obs_id, original_value, sensor = row
        tampered_value = original_value * 0.5  # Halve the value

        print(f"[*] Tampering health observation {obs_id}")
        print(f"    Sensor: {sensor}")
        print(f"    Original value: {original_value:.4f}")
        print(f"    Tampered value: {tampered_value:.4f}")

        # Use admin role to bypass app-level protections
        cur.execute(
            "UPDATE health_observations SET value = %s WHERE id = %s",
            (tampered_value, obs_id),
        )
        conn.commit()

        print("[+] Health reading tampered successfully.")
        print("[+] Now verify the Evidence Passport for A-017-ENG-02.")
        print("    The verification should show TAMPERED status.")
        print("")
        print("    To verify via API:")
        print("    POST /api/v1/passport/verify")
        print("    Or use the Verify button in the UI.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
