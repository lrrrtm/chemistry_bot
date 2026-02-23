import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime

import telebot


def get_settings_path() -> str:
    root = os.getenv("ROOT_FOLDER", ".")
    return os.path.join(root, "data", "backup_settings.json")


def load_settings() -> dict:
    path = get_settings_path()
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {"time": "", "chat_id": ""}


def save_settings(settings: dict) -> None:
    path = get_settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(settings, f)


def run_backup() -> dict:
    """Create backup zip and send to Telegram. Returns {ok, error?}."""
    root        = os.getenv("ROOT_FOLDER", ".")
    db_host     = os.getenv("DB_HOST",     "db")
    db_user     = os.getenv("DB_USER",     "chemistry")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name     = os.getenv("DB_NAME",     "chemistry_bot")
    bot_token   = os.getenv("BOT_API_KEY")

    settings = load_settings()
    chat_id  = settings.get("chat_id", "").strip()

    if not chat_id:
        return {"ok": False, "error": "chat_id не задан в настройках"}
    if not bot_token:
        return {"ok": False, "error": "BOT_API_KEY не задан"}

    temp_dir = tempfile.mkdtemp()
    try:
        # ── Dump DB ───────────────────────────────────────────────────────────
        sql_path = os.path.join(temp_dir, "backup.sql")
        with open(sql_path, "wb") as sql_out:
            result = subprocess.run(
                ["mysqldump", f"-h{db_host}", f"-u{db_user}", f"-p{db_password}",
                 "--skip-ssl", db_name],
                stdout=sql_out,
                stderr=subprocess.PIPE,
                timeout=300,
            )
        if result.returncode != 0:
            return {"ok": False,
                    "error": f"mysqldump: {result.stderr.decode(errors='replace')}"}

        # ── Pack into zip ─────────────────────────────────────────────────────
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path  = os.path.join(temp_dir, f"chembot_backup_{timestamp}.zip")

        image_dirs = {
            "images/answers":   os.path.join(root, "data", "images", "answers"),
            "images/questions": os.path.join(root, "data", "images", "questions"),
            "images/users":     os.path.join(root, "data", "images", "users"),
        }

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(sql_path, "backup.sql")
            for zip_folder, src_dir in image_dirs.items():
                if os.path.isdir(src_dir):
                    for fname in os.listdir(src_dir):
                        fpath = os.path.join(src_dir, fname)
                        if os.path.isfile(fpath):
                            zf.write(fpath, f"{zip_folder}/{fname}")

        # ── Send to Telegram ──────────────────────────────────────────────────
        bot = telebot.TeleBot(token=bot_token)
        with open(zip_path, "rb") as f:
            bot.send_document(
                chat_id=chat_id,
                document=f,
                visible_file_name=f"chembot_backup_{timestamp}.zip",
                caption=(
                    f"Резервная копия системы от "
                    f"{datetime.now().strftime('%d.%m.%Y %H:%M')} UTC"
                ),
            )
        return {"ok": True}

    except Exception as e:
        return {"ok": False, "error": str(e)}

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
