"""AERIS Backend — Security Tests.

Tests for auth, RBAC, audit, CSRF, lockout, security headers, and more.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.core.audit import GENESIS_HASH, verify_audit_chain, write_audit_entry
from app.core.crypto import canonical_json, decrypt_field, encrypt_field, sha256_hash_str
from app.core.rbac import ROLE_PERMISSIONS, Permission, Role, has_permission
from app.core.security import (
    check_password_policy,
    constant_time_compare,
    create_access_token,
    decode_access_token,
    generate_csrf_token,
    hash_password,
    hash_token,
    verify_password,
)


# ── Password Hashing Tests ──────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_and_verify(self) -> None:
        password = "SecurePassword123!"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self) -> None:
        hashed = hash_password("CorrectPassword1!")
        assert not verify_password("WrongPassword1!", hashed)

    def test_constant_time_comparison(self) -> None:
        assert constant_time_compare("abc", "abc")
        assert not constant_time_compare("abc", "def")


class TestPasswordPolicy:
    def test_valid_password(self) -> None:
        violations = check_password_policy("StrongPass1234!")
        assert len(violations) == 0

    def test_too_short(self) -> None:
        violations = check_password_policy("Short1!")
        assert any("12" in v for v in violations)

    def test_no_uppercase(self) -> None:
        violations = check_password_policy("alllowercase123!")
        assert any("uppercase" in v for v in violations)


# ── JWT Tests ────────────────────────────────────────────────────────

class TestJWT:
    @patch("app.core.security.get_settings")
    def test_create_and_decode_access_token(self, mock_settings) -> None:  # type: ignore[no-untyped-def]
        mock_settings.return_value.jwt_signing_key = "test-secret-key-for-jwt-testing-1234"
        mock_settings.return_value.jwt_access_token_expire_minutes = 10

        token = create_access_token("user-123", "FLEET_SUPERVISOR", "test_user")
        payload = decode_access_token(token)

        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["role"] == "FLEET_SUPERVISOR"
        assert payload["username"] == "test_user"
        assert payload["type"] == "access"

    @patch("app.core.security.get_settings")
    def test_expired_token_returns_none(self, mock_settings) -> None:  # type: ignore[no-untyped-def]
        mock_settings.return_value.jwt_signing_key = "test-secret-key-for-jwt-testing-1234"
        mock_settings.return_value.jwt_access_token_expire_minutes = -1  # Already expired

        token = create_access_token("user-123", "FLEET_SUPERVISOR", "test_user")
        payload = decode_access_token(token)
        assert payload is None

    def test_invalid_token_returns_none(self) -> None:
        payload = decode_access_token("invalid.token.here")
        assert payload is None


class TestTokenHashing:
    def test_hash_is_deterministic(self) -> None:
        token = "test-token-value"
        assert hash_token(token) == hash_token(token)

    def test_different_tokens_different_hashes(self) -> None:
        assert hash_token("token-a") != hash_token("token-b")


# ── CSRF Tests ───────────────────────────────────────────────────────

class TestCSRF:
    def test_csrf_token_generation(self) -> None:
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        assert token1 != token2
        assert len(token1) > 20


# ── RBAC Tests ───────────────────────────────────────────────────────

class TestRBAC:
    def test_fleet_supervisor_has_all_fleet_permissions(self) -> None:
        assert has_permission("FLEET_SUPERVISOR", Permission.VIEW_FLEET)
        assert has_permission("FLEET_SUPERVISOR", Permission.MAKE_DECISION)
        assert has_permission("FLEET_SUPERVISOR", Permission.APPROVE_OVERRIDE)
        assert has_permission("FLEET_SUPERVISOR", Permission.VIEW_TECH_NOTES)

    def test_sys_admin_cannot_make_decisions(self) -> None:
        """Separation of duties: SYS_ADMIN cannot make maintenance decisions."""
        assert not has_permission("SYS_ADMIN", Permission.MAKE_DECISION)
        assert not has_permission("SYS_ADMIN", Permission.APPROVE_OVERRIDE)

    def test_sys_admin_can_manage_users(self) -> None:
        assert has_permission("SYS_ADMIN", Permission.MANAGE_USERS)
        assert has_permission("SYS_ADMIN", Permission.MANAGE_CONFIG)
        assert has_permission("SYS_ADMIN", Permission.INGEST_DATA)

    def test_spares_planner_cannot_view_tech_notes(self) -> None:
        assert not has_permission("SPARES_PLANNER", Permission.VIEW_TECH_NOTES)
        assert has_permission("SPARES_PLANNER", Permission.EDIT_SPARES)

    def test_maint_engineer_cannot_approve_overrides(self) -> None:
        assert not has_permission("MAINT_ENGINEER", Permission.APPROVE_OVERRIDE)
        assert has_permission("MAINT_ENGINEER", Permission.MAKE_DECISION)

    def test_maint_planner_can_edit_facilities(self) -> None:
        assert has_permission("MAINT_PLANNER", Permission.EDIT_FACILITIES)
        assert not has_permission("MAINT_PLANNER", Permission.APPROVE_OVERRIDE)

    def test_invalid_role_denied(self) -> None:
        assert not has_permission("INVALID_ROLE", Permission.VIEW_FLEET)

    def test_all_roles_have_view_fleet(self) -> None:
        """Every role should at least be able to see the fleet."""
        for role in Role:
            assert has_permission(role.value, Permission.VIEW_FLEET), f"{role} missing VIEW_FLEET"

    def test_deny_by_default(self) -> None:
        """Roles should not have permissions not explicitly granted."""
        assert not has_permission("SPARES_PLANNER", Permission.RUN_INFERENCE)
        assert not has_permission("SPARES_PLANNER", Permission.MANAGE_USERS)


# ── Crypto Tests ─────────────────────────────────────────────────────

class TestCrypto:
    def test_canonical_json_sorted(self) -> None:
        obj = {"b": 2, "a": 1, "c": 3}
        result = canonical_json(obj)
        assert result == '{"a":1,"b":2,"c":3}'

    def test_sha256_hash(self) -> None:
        result = sha256_hash_str("test data")
        assert len(result) == 64
        assert result == hashlib.sha256(b"test data").hexdigest()

    @patch("app.core.crypto.read_json_secret")
    def test_encrypt_decrypt_roundtrip(self, mock_secret) -> None:  # type: ignore[no-untyped-def]
        # 32-byte key (hex-encoded = 64 chars)
        test_key = "0" * 64
        mock_secret.return_value = {"key_id": "test-k1", "key": test_key}

        plaintext = "Sensitive technician notes about bearing wear"
        encrypted = encrypt_field(plaintext)
        assert encrypted != plaintext
        assert "test-k1:" in encrypted

        decrypted = decrypt_field(encrypted)
        assert decrypted == plaintext

    @patch("app.core.crypto.read_json_secret")
    def test_empty_string_encrypt(self, mock_secret) -> None:  # type: ignore[no-untyped-def]
        mock_secret.return_value = {"key_id": "k1", "key": "0" * 64}
        assert encrypt_field("") == ""
        assert decrypt_field("") == ""


# ── Audit Chain Tests ────────────────────────────────────────────────

class TestAuditChain:
    def test_genesis_hash_is_deterministic(self) -> None:
        expected = hashlib.sha256(b"VAYU-PdM-GENESIS").hexdigest()
        assert GENESIS_HASH == expected
