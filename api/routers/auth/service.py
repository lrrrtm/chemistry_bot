import hashlib
import hmac
import os
import re
import secrets
import string
from datetime import datetime

import telebot

import api.config as _config


def create_token(admin_id: str) -> str:
    """Create a simple HMAC token: <admin_id>:<timestamp>.<signature>"""
    timestamp = str(int(datetime.utcnow().timestamp()))
    payload = f"{admin_id}:{timestamp}"
    sig = hmac.new(_config.SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_token(token: str) -> bool:
    """Verify HMAC token (valid for 24 hours)."""
    try:
        payload, sig = token.rsplit(".", 1)
        admin_id, timestamp = payload.split(":", 1)
        expected_sig = hmac.new(
            _config.SECRET_KEY.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return False
        age = datetime.utcnow().timestamp() - int(timestamp)
        return age < 86400  # 24 h
    except Exception:
        return False


def generate_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def send_password_to_admin(password: str) -> None:
    """Send new password to admin via Telegram. Raises on failure."""
    bot_token = os.getenv("BOT_API_KEY")
    admin_id = os.getenv("ADMIN_ID")
    if not bot_token:
        raise RuntimeError("BOT_API_KEY не задан")
    if not admin_id:
        raise RuntimeError("ADMIN_ID не задан")
    bot = telebot.TeleBot(token=bot_token)
    bot.send_message(
        chat_id=int(admin_id),
        text=(
            "🔑 <b>Восстановление пароля панели администратора</b>\n\n"
            f"Ваш новый пароль:\n<code>{password}</code>"
        ),
        parse_mode="HTML",
    )


def update_env_password(new_password: str, env_path: str) -> None:
    """Update PANEL_PASSWORD line in .env file."""
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
        if re.search(r"^PANEL_PASSWORD=", content, re.MULTILINE):
            content = re.sub(
                r"^PANEL_PASSWORD=.*$",
                f"PANEL_PASSWORD={new_password}",
                content,
                flags=re.MULTILINE,
            )
        else:
            content += f"\nPANEL_PASSWORD={new_password}\n"
        with open(env_path, "w") as f:
            f.write(content)
    else:
        with open(env_path, "w") as f:
            f.write(f"PANEL_PASSWORD={new_password}\n")
