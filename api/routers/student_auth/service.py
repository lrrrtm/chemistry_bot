from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta

import api.config as _config


STUDENT_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 30
INVITE_TTL_HOURS = 72
TELEGRAM_LINK_TTL_MINUTES = 30
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,32}$")
ACCESS_GRANT_PURPOSE_ADMIN_INVITE = "admin_invite"
ACCESS_GRANT_PURPOSE_SELF_WEB_ACCESS = "self_web_access"
WEB_ACCESS_GRANT_PURPOSES = {
    ACCESS_GRANT_PURPOSE_ADMIN_INVITE,
    ACCESS_GRANT_PURPOSE_SELF_WEB_ACCESS,
}


def normalize_username(raw_username: str) -> str:
    username = raw_username.strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Логин должен быть длиной 3-32 символа и содержать только буквы, цифры и _")
    return username.lower()


def validate_password(raw_password: str) -> str:
    password = raw_password.strip()
    if len(password) < 6 or len(password) > 128:
        raise ValueError("Пароль должен быть длиной от 6 до 128 символов")
    return password


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"pbkdf2_sha256${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        scheme, salt_b64, digest_b64 = password_hash.split("$", 2)
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_student_token(user_id: int, token_version: int = 0) -> str:
    timestamp = str(int(datetime.now(UTC).timestamp()))
    payload = f"student:{user_id}:{timestamp}:{token_version}"
    signature = hmac.new(_config.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def verify_student_token(token: str) -> tuple[int, int] | None:
    try:
        payload, signature = token.rsplit(".", 1)
        expected_signature = hmac.new(_config.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None

        parts = payload.split(":")
        if len(parts) == 3:
            scope, user_id, timestamp = parts
            token_version = 0
        elif len(parts) == 4:
            scope, user_id, timestamp, token_version = parts
        else:
            return None
        if scope != "student":
            return None

        age = datetime.now(UTC).timestamp() - int(timestamp)
        if age < 0 or age > STUDENT_TOKEN_TTL_SECONDS:
            return None

        return int(user_id), int(token_version)
    except Exception:
        return None


def generate_one_time_token() -> str:
    return secrets.token_urlsafe(24)


def hash_one_time_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def invite_expiration() -> datetime:
    return datetime.now() + timedelta(hours=INVITE_TTL_HOURS)


def telegram_link_expiration() -> datetime:
    return datetime.now() + timedelta(minutes=TELEGRAM_LINK_TTL_MINUTES)
