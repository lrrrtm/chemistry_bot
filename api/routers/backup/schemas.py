from pydantic import BaseModel


class BackupSettings(BaseModel):
    time: str           # "HH:MM" or ""
    chat_id: str        # Telegram chat ID
    yadisk_token: str = ""  # Yandex Disk OAuth token
