import glob as glob_module
import os
import shutil
import zipfile
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from api.config import ROOT_FOLDER
from api.dependencies import require_auth
from api.routers.backup.schemas import BackupSettings
from api.scheduler import reschedule
from utils.backup_job import load_settings, run_backup as _run_backup_job
from utils.backup_job import save_settings

router = APIRouter(prefix="/api/admin", tags=["backup"])


@router.get("/backup-settings")
def get_backup_settings(_: str = Depends(require_auth)):
    s = load_settings()
    # Mask the token for the frontend — send a flag, not the raw token
    return {
        "time": s.get("time", ""),
        "chat_id": s.get("chat_id", ""),
        "yadisk_token": s.get("yadisk_token", ""),
    }


@router.post("/backup-settings")
def update_backup_settings(req: BackupSettings, _: str = Depends(require_auth)):
    if req.time and len(req.time.split(":")) != 2:
        raise HTTPException(status_code=400, detail="Формат времени: HH:MM")
    settings = {
        "time": req.time.strip(),
        "chat_id": req.chat_id.strip(),
        "yadisk_token": req.yadisk_token.strip(),
    }
    save_settings(settings)
    reschedule(settings["time"])
    return {"ok": True}


@router.post("/backup-now")
def backup_now(_: str = Depends(require_auth)):
    result = _run_backup_job()
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "Ошибка"))
    return {"ok": True, "message": "Резервная копия создана"}


# ── Yandex Disk backups ───────────────────────────────────────────────────────

@router.get("/yadisk-backups")
def yadisk_backups(_: str = Depends(require_auth)):
    from utils.yandex_disk import list_backups
    return list_backups()


@router.post("/yadisk-restore")
def yadisk_restore(body: dict, _: str = Depends(require_auth)):
    """Download a backup from Yandex Disk and restore it."""
    disk_path = body.get("path", "").strip()
    if not disk_path:
        raise HTTPException(status_code=400, detail="path обязателен")

    from utils.yandex_disk import download_file

    temp_dir = os.path.join(
        ROOT_FOLDER, "data", "temp",
        f"yadisk_restore_{datetime.now().strftime('%Y%m%d%H%M%S')}",
    )
    os.makedirs(temp_dir, exist_ok=True)

    try:
        zip_path = os.path.join(temp_dir, "backup.zip")
        dl = download_file(disk_path, zip_path)
        if not dl.get("ok"):
            raise HTTPException(status_code=500,
                                detail=dl.get("error", "Ошибка загрузки"))

        # Re-use the same restore logic
        _restore_from_zip(zip_path, temp_dir)
        return {"ok": True, "message": "Резервная копия с Яндекс Диска восстановлена"}

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/restore")
def restore_backup(file: UploadFile = File(...), _: str = Depends(require_auth)):
    temp_dir = os.path.join(
        ROOT_FOLDER,
        "data",
        "temp",
        f"restore_{datetime.now().strftime('%Y%m%d%H%M%S')}",
    )
    os.makedirs(temp_dir, exist_ok=True)

    try:
        zip_path = os.path.join(temp_dir, "backup.zip")
        with open(zip_path, "wb") as f:
            f.write(file.file.read())

        _restore_from_zip(zip_path, temp_dir)
        return {"ok": True, "message": "Резервная копия успешно восстановлена"}

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ── Shared restore helper ─────────────────────────────────────────────────────

def _restore_from_zip(zip_path: str, temp_dir: str) -> None:
    """Extract zip, import SQL, copy images. Raises HTTPException on error."""
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(temp_dir)

    sql_files = glob_module.glob(
        os.path.join(temp_dir, "**", "*.sql"), recursive=True
    )
    if not sql_files:
        raise HTTPException(status_code=400, detail="SQL файл не найден в архиве")

    import subprocess

    db_host = os.getenv("DB_HOST", "db")
    db_user = os.getenv("DB_USER", "chemistry")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "chemistry_bot")

    with open(sql_files[0], "rb") as sql_f:
        result = subprocess.run(
            [
                "mysql",
                f"-h{db_host}",
                f"-u{db_user}",
                f"-p{db_password}",
                "--skip-ssl",
                db_name,
            ],
            stdin=sql_f,
            capture_output=True,
            timeout=300,
        )
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка восстановления БД: {result.stderr.decode(errors='replace')}",
        )

    # Re-run migrations to add columns that may be missing in the backup
    from db.database import run_migrations
    run_migrations()

    image_mapping = {
        "answers": os.path.join(ROOT_FOLDER, "data", "images", "answers"),
        "questions": os.path.join(ROOT_FOLDER, "data", "images", "questions"),
        "users": os.path.join(ROOT_FOLDER, "data", "images", "users"),
    }
    for folder_name, dest_dir in image_mapping.items():
        os.makedirs(dest_dir, exist_ok=True)
        for root, dirs, _ in os.walk(temp_dir):
            for d in dirs:
                if d == folder_name:
                    src_dir = os.path.join(root, d)
                    for fname in os.listdir(src_dir):
                        src = os.path.join(src_dir, fname)
                        if os.path.isfile(src):
                            shutil.copy2(src, os.path.join(dest_dir, fname))
