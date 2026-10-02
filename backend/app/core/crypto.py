"""AERIS Backend — Cryptography Module.

AES-256-GCM field-level encryption with versioned key IDs,
Ed25519 signing for Evidence Passports, and HMAC-SHA256 for model integrity.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import read_json_secret, read_secret
from app.core.logging import get_logger

logger = get_logger("crypto")


# ── AES-256-GCM Field Encryption ────────────────────────────────────

def _get_aes_key() -> tuple[str, bytes]:
    """Get AES key and key ID from secrets."""
    config = read_json_secret("aes_encryption_key")
    key_id = config.get("key_id", "k1")
    key_hex = config.get("key", "")
    if not key_hex:
        raise RuntimeError("AES encryption key not configured")
    return key_id, bytes.fromhex(key_hex)


def encrypt_field(plaintext: str) -> str:
    """Encrypt a field value with AES-256-GCM.
    
    Returns: base64(key_id:nonce:ciphertext:tag)
    """
    if not plaintext:
        return ""
    key_id, key = _get_aes_key()
    nonce = os.urandom(12)  # 96-bit nonce
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Pack: key_id + nonce + ciphertext (includes 16-byte tag)
    packed = f"{key_id}:{base64.b64encode(nonce).decode()}:{base64.b64encode(ciphertext).decode()}"
    return packed


def decrypt_field(encrypted: str) -> str:
    """Decrypt a field value encrypted with AES-256-GCM."""
    if not encrypted:
        return ""
    try:
        parts = encrypted.split(":")
        if len(parts) != 3:
            logger.error("Invalid encrypted field format")
            return "[DECRYPTION ERROR]"
        _key_id, nonce_b64, ciphertext_b64 = parts
        _, key = _get_aes_key()
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except Exception as e:
        logger.error(f"Decryption failed: {type(e).__name__}")
        return "[DECRYPTION ERROR]"


# ── Ed25519 Signing (Evidence Passports) ─────────────────────────────

def _load_ed25519_private_key() -> Ed25519PrivateKey:
    """Load the Ed25519 private key from secrets."""
    key_pem = read_secret("ed25519_private_key")
    if not key_pem:
        raise RuntimeError("Ed25519 private key not configured")
    return serialization.load_pem_private_key(
        key_pem.encode(), password=None
    )  # type: ignore[return-value]


def _load_ed25519_public_key() -> Ed25519PublicKey:
    """Load the Ed25519 public key from secrets."""
    key_pem = read_secret("ed25519_public_key")
    if not key_pem:
        raise RuntimeError("Ed25519 public key not configured")
    return serialization.load_pem_public_key(
        key_pem.encode()
    )  # type: ignore[return-value]


def sign_data(data: bytes) -> str:
    """Sign data with Ed25519 and return base64-encoded signature."""
    private_key = _load_ed25519_private_key()
    signature = private_key.sign(data)
    return base64.b64encode(signature).decode()


def verify_signature(data: bytes, signature_b64: str) -> bool:
    """Verify an Ed25519 signature."""
    try:
        public_key = _load_ed25519_public_key()
        signature = base64.b64decode(signature_b64)
        public_key.verify(signature, data)
        return True
    except Exception:
        return False


# ── HMAC-SHA256 (Model Integrity) ────────────────────────────────────

def compute_hmac(data: bytes) -> str:
    """Compute HMAC-SHA256 of data using the model registry key."""
    key = read_secret("model_hmac_key").encode()
    if not key:
        raise RuntimeError("Model HMAC key not configured")
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def verify_hmac(data: bytes, expected_hmac: str) -> bool:
    """Verify HMAC-SHA256 in constant time."""
    computed = compute_hmac(data)
    return hmac.compare_digest(computed, expected_hmac)


# ── Hashing Utilities ────────────────────────────────────────────────

def sha256_hash(data: bytes) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def sha256_hash_str(data: str) -> str:
    """Compute SHA-256 hash of string data."""
    return sha256_hash(data.encode("utf-8"))


def canonical_json(obj: Any) -> str:
    """Produce canonical JSON for hashing (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
