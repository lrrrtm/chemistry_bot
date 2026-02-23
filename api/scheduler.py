from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from utils.backup_job import load_settings
from utils.backup_job import run_backup as _run_backup_job

_scheduler = BackgroundScheduler(timezone="UTC")


def reschedule(time_str: str) -> None:
    if _scheduler.get_job("daily_backup"):
        _scheduler.remove_job("daily_backup")
    if time_str:
        hour, minute = time_str.split(":", 1)
        _scheduler.add_job(
            _run_backup_job,
            "cron",
            hour=int(hour),
            minute=int(minute),
            id="daily_backup",
            replace_existing=True,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _scheduler.start()
    settings = load_settings()
    if settings.get("time"):
        reschedule(settings["time"])
    yield
    _scheduler.shutdown(wait=False)
