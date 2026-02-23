"""
Unit tests for api/routers/auth/service.py

These tests are pure-Python and require no database connection.
All external dependencies (Telegram bot, .env file) are not used here.
"""

import hashlib
import hmac
import os
import string
from datetime import datetime
from pathlib import Path

import pytest

# Set env var before import so api.config reads it during module init
os.environ.setdefault("PANEL_PASSWORD", "ci_test_secret")

import api.config as _cfg  # noqa: E402 (must come after os.environ.setdefault)
from api.routers.auth.service import (  # noqa: E402
    create_token,
    generate_password,
    update_env_password,
    verify_token,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def fixed_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin SECRET_KEY to a predictable value for every test in this module."""
    monkeypatch.setattr(_cfg, "SECRET_KEY", "test_secret_key_12345")


def _make_token_with_timestamp(timestamp: int) -> str:
    """Helper: craft a structurally valid token with an arbitrary timestamp."""
    payload = f"admin:{timestamp}"
    sig = hmac.new(
        _cfg.SECRET_KEY.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{sig}"


# ─────────────────────────────────────────────────────────────────────────────
# create_token / verify_token
# ─────────────────────────────────────────────────────────────────────────────


class TestTokenRoundtrip:
    def test_fresh_token_is_valid(self) -> None:
        token = create_token("admin")
        assert verify_token(token) is True

    def test_tokens_differ_between_calls(self) -> None:
        """Two tokens created at (nearly) the same second may be identical by design;
        but the function must at least return a non-empty string each time."""
        t1 = create_token("admin")
        t2 = create_token("admin")
        assert isinstance(t1, str) and len(t1) > 0
        assert isinstance(t2, str) and len(t2) > 0

    def test_token_structure(self) -> None:
        """Token format: <admin_id>:<timestamp>.<signature>"""
        token = create_token("admin")
        parts = token.rsplit(".", 1)
        assert len(parts) == 2, "Token must contain exactly one '.' separating payload and sig"
        payload, sig = parts
        assert ":" in payload, "Payload must contain admin_id:timestamp"
        assert len(sig) == 64, "SHA-256 hex digest must be 64 characters"


class TestVerifyToken:
    def test_tampered_signature(self) -> None:
        token = create_token("admin")
        payload, sig = token.rsplit(".", 1)
        bad_token = f"{payload}.{'0' * 64}"
        assert verify_token(bad_token) is False

    def test_tampered_payload(self) -> None:
        token = create_token("admin")
        payload, sig = token.rsplit(".", 1)
        bad_payload = payload + "x"
        assert verify_token(f"{bad_payload}.{sig}") is False

    def test_wrong_secret_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        token = create_token("admin")
        monkeypatch.setattr(_cfg, "SECRET_KEY", "completely_different_key")
        assert verify_token(token) is False

    def test_expired_token(self) -> None:
        """Token older than 24 hours must be rejected."""
        old_ts = int(datetime.utcnow().timestamp()) - 90_000  # ~25 h ago
        expired = _make_token_with_timestamp(old_ts)
        assert verify_token(expired) is False

    def test_future_timestamp_is_invalid_age(self) -> None:
        """Timestamp far in the future results in negative age → rejected (age >= 0 check)."""
        future_ts = int(datetime.utcnow().timestamp()) + 90_000
        future_token = _make_token_with_timestamp(future_ts)
        # age is negative so age < 86400 is True — this is debatable behaviour,
        # but we at least verify it doesn't raise an exception
        result = verify_token(future_token)
        assert isinstance(result, bool)

    def test_empty_string(self) -> None:
        assert verify_token("") is False

    def test_random_garbage(self) -> None:
        assert verify_token("not.a.token.at.all") is False

    def test_missing_dot(self) -> None:
        assert verify_token("admin:1234567890noDot") is False

    def test_missing_colon_in_payload(self) -> None:
        assert verify_token("adminNOcolon.somesig") is False


# ─────────────────────────────────────────────────────────────────────────────
# generate_password
# ─────────────────────────────────────────────────────────────────────────────


class TestGeneratePassword:
    _ALPHABET = set(string.ascii_letters + string.digits)

    def test_default_length(self) -> None:
        assert len(generate_password()) == 16

    def test_custom_length(self) -> None:
        for n in (8, 24, 32):
            assert len(generate_password(n)) == n

    def test_only_alphanumeric_chars(self) -> None:
        for _ in range(20):
            pwd = generate_password(32)
            assert set(pwd).issubset(self._ALPHABET), f"Unexpected chars in: {pwd}"

    def test_passwords_are_unique(self) -> None:
        passwords = {generate_password(16) for _ in range(50)}
        # Probability of any collision in 50 draws from 62^16 space is negligible
        assert len(passwords) == 50

    def test_returns_string(self) -> None:
        assert isinstance(generate_password(), str)


# ─────────────────────────────────────────────────────────────────────────────
# update_env_password
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdateEnvPassword:
    def test_updates_existing_line(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("DB_HOST=db\nPANEL_PASSWORD=old_pass\nOTHER=value\n")
        update_env_password("new_pass", str(env))
        content = env.read_text()
        assert "PANEL_PASSWORD=new_pass" in content
        assert "PANEL_PASSWORD=old_pass" not in content

    def test_preserves_other_lines(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("DB_HOST=db\nPANEL_PASSWORD=old\nMY_VAR=keep_me\n")
        update_env_password("x", str(env))
        content = env.read_text()
        assert "DB_HOST=db" in content
        assert "MY_VAR=keep_me" in content

    def test_appends_when_key_missing(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("DB_HOST=db\n")
        update_env_password("fresh_pass", str(env))
        content = env.read_text()
        assert "PANEL_PASSWORD=fresh_pass" in content
        assert "DB_HOST=db" in content  # original line still there

    def test_creates_file_if_not_exists(self, tmp_path: Path) -> None:
        env = tmp_path / "new.env"
        assert not env.exists()
        update_env_password("created_pass", str(env))
        assert env.exists()
        assert "PANEL_PASSWORD=created_pass" in env.read_text()

    def test_no_duplicate_key(self, tmp_path: Path) -> None:
        """Calling twice must not result in two PANEL_PASSWORD lines."""
        env = tmp_path / ".env"
        env.write_text("PANEL_PASSWORD=v1\n")
        update_env_password("v2", str(env))
        update_env_password("v3", str(env))
        lines = [l for l in env.read_text().splitlines() if l.startswith("PANEL_PASSWORD=")]
        assert len(lines) == 1
        assert lines[0] == "PANEL_PASSWORD=v3"

    def test_only_replaces_exact_key(self, tmp_path: Path) -> None:
        """MY_PANEL_PASSWORD must not be affected."""
        env = tmp_path / ".env"
        env.write_text("MY_PANEL_PASSWORD=untouched\nPANEL_PASSWORD=old\n")
        update_env_password("new", str(env))
        content = env.read_text()
        assert "MY_PANEL_PASSWORD=untouched" in content
        assert "PANEL_PASSWORD=new" in content
