"""Yandex Disk helpers – upload / list / download backups."""

import logging
import os
from typing import Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

YADISK_API = "https://cloud-api.yandex.net/v1/disk/resources"
BACKUP_FOLDER = "app:/"


def _token() -> Optional[str]:
    """Return the OAuth token from settings, or None."""
    from utils.backup_job import load_settings

    return (load_settings().get("yadisk_token") or "").strip() or None


def _headers(token: str) -> dict:
    return {"Authorization": f"OAuth {token}", "Accept": "application/json"}


# ── Upload ─────────────────────────────────────────────────────────────────────

def upload_file(local_path: str, disk_filename: str,
                token: Optional[str] = None) -> dict:
    """Upload *local_path* to BACKUP_FOLDER/disk_filename on Yandex Disk.

    Returns ``{"ok": True}`` or ``{"ok": False, "error": "..."}``
    """
    token = token or _token()
    if not token:
        return {"ok": False, "error": "Yandex Disk токен не задан"}

    try:
        disk_path = f"{BACKUP_FOLDER}{disk_filename}"

        # Step 1 — get upload URL
        r = requests.get(
            f"{YADISK_API}/upload",
            params={"path": disk_path, "overwrite": "true"},
            headers=_headers(token),
            timeout=15,
        )
        r.raise_for_status()
        href = r.json()["href"]

        # Step 2 — PUT file
        with open(local_path, "rb") as f:
            r2 = requests.put(href, data=f, timeout=600)
        r2.raise_for_status()

        logger.info("Uploaded %s → yadisk:%s", local_path, disk_path)
        return {"ok": True}

    except Exception as e:
        logger.exception("Yandex Disk upload error")
        return {"ok": False, "error": str(e)}


# ── List ───────────────────────────────────────────────────────────────────────

def list_backups(token: Optional[str] = None, limit: int = 100) -> list[dict]:
    """Return list of backups in BACKUP_FOLDER, newest first.

    Each item: ``{name, path, size, modified, created}``
    """
    token = token or _token()
    if not token:
        return []

    try:
        r = requests.get(
            YADISK_API,
            params={
                "path": BACKUP_FOLDER,
                "limit": limit,
                "sort": "-modified",
                "fields": "_embedded.items.name,_embedded.items.path,_embedded.items.size,_embedded.items.modified,_embedded.items.created",
            },
            headers=_headers(token),
            timeout=15,
        )
        r.raise_for_status()
        items = r.json().get("_embedded", {}).get("items", [])

        return [
            {
                "name": it["name"],
                "path": it["path"],
                "size": it.get("size", 0),
                "modified": it.get("modified", ""),
                "created": it.get("created", ""),
            }
            for it in items
            if it["name"].endswith(".zip")
        ]
    except Exception:
        logger.exception("Yandex Disk list error")
        return []


# ── Download ───────────────────────────────────────────────────────────────────

def download_file(disk_path: str, local_path: str,
                  token: Optional[str] = None) -> dict:
    """Download *disk_path* from Yandex Disk to *local_path*.

    Returns ``{"ok": True}`` or ``{"ok": False, "error": "..."}``
    """
    token = token or _token()
    if not token:
        return {"ok": False, "error": "Yandex Disk токен не задан"}

    try:
        # Step 1 — get download URL
        r = requests.get(
            f"{YADISK_API}/download",
            params={"path": disk_path},
            headers=_headers(token),
            timeout=15,
        )
        r.raise_for_status()
        href = r.json()["href"]

        # Step 2 — stream content to file
        with requests.get(href, stream=True, timeout=600) as dl:
            dl.raise_for_status()
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                for chunk in dl.iter_content(chunk_size=1024 * 256):
                    f.write(chunk)

        logger.info("Downloaded yadisk:%s → %s", disk_path, local_path)
        return {"ok": True}

    except Exception as e:
        logger.exception("Yandex Disk download error")
        return {"ok": False, "error": str(e)}


# ── Delete ─────────────────────────────────────────────────────────────────────

def delete_file(disk_path: str, token: Optional[str] = None) -> dict:
    """Delete file on Yandex Disk. Returns ``{"ok": True/False}``."""
    token = token or _token()
    if not token:
        return {"ok": False, "error": "Yandex Disk токен не задан"}

    try:
        r = requests.delete(
            YADISK_API,
            params={"path": disk_path, "permanently": "true"},
            headers=_headers(token),
            timeout=15,
        )
        r.raise_for_status()
        return {"ok": True}
    except Exception as e:
        logger.exception("Yandex Disk delete error")
        return {"ok": False, "error": str(e)}
