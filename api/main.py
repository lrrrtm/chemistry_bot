import hashlib
import glob as glob_module
import os
import shutil
import subprocess
import sys
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Header, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

import telebot

from db.crud import (
    get_all_users, remove_user, get_user_works, get_topics_table, get_all_pool,
    get_all_questions, insert_new_hand_work, get_question_from_pool,
    deactivate_question, update_question, switch_image_flag, insert_question_into_pool,
    get_ege_converting, update_ege_converting, get_work_questions_joined_pool,
    get_work_by_url_data, get_user, get_hand_work, get_topic_by_id, get_work_questions,
    get_output_mark, get_all_topics, insert_topics_data, insert_pool_data,
    create_topic, deactivate_topic, update_topic,
)
from db.models import Pool
from utils.clearing import clear_folder
from utils.excel import export_topics_list, import_topics_list, import_pool
from utils.image_converter import image_to_base64
from utils.move_file import move_image
from utils.tags_helper import get_random_questions, get_random_questions_for_hard_tags_filter
from utils.user_statistics import get_user_statistics
from utils.backup_job import load_settings, save_settings, run_backup as _run_backup_job


# ──────────────────────────────────────────────────────────────────────────────
# Scheduler
# ──────────────────────────────────────────────────────────────────────────────

_scheduler = BackgroundScheduler(timezone="UTC")


def _reschedule(time_str: str) -> None:
    if _scheduler.get_job("daily_backup"):
        _scheduler.remove_job("daily_backup")
    if time_str:
        hour, minute = time_str.split(":", 1)
        _scheduler.add_job(
            _run_backup_job, "cron",
            hour=int(hour), minute=int(minute),
            id="daily_backup",
            replace_existing=True,
        )


@asynccontextmanager
async def lifespan(app):
    _scheduler.start()
    settings = load_settings()
    if settings.get("time"):
        _reschedule(settings["time"])
    yield
    _scheduler.shutdown(wait=False)


# ──────────────────────────────────────────────────────────────────────────────
# Auth helpers
# ──────────────────────────────────────────────────────────────────────────────

SECRET_KEY = os.getenv("PANEL_PASSWORD", "changeme")
ROOT_FOLDER = os.getenv("ROOT_FOLDER", ".")

import hmac as _hmac


def create_token(admin_id: str) -> str:
    """Create a simple HMAC token: <timestamp>.<signature>"""
    timestamp = str(int(datetime.utcnow().timestamp()))
    payload = f"{admin_id}:{timestamp}"
    sig = _hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_token(token: str) -> bool:
    """Verify HMAC token (valid for 24 hours)."""
    try:
        payload, sig = token.rsplit(".", 1)
        admin_id, timestamp = payload.split(":", 1)
        expected_sig = _hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not _hmac.compare_digest(sig, expected_sig):
            return False
        ts = int(timestamp)
        age = datetime.utcnow().timestamp() - ts
        return age < 86400  # 24h
    except Exception:
        return False


def require_auth(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = authorization.removeprefix("Bearer ").strip()
    if not verify_token(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return token


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schemas
# ──────────────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


class QuestionUpdate(BaseModel):
    text: str
    answer: str
    level: int
    full_mark: int
    tags_list: List[str]
    is_rotate: int
    is_selfcheck: int


class NewQuestion(BaseModel):
    text: str
    answer: str
    type: str
    level: int
    full_mark: int
    tags_list: List[str]
    is_rotate: bool = False
    is_selfcheck: bool = False


class HandWorkCreate(BaseModel):
    name: str
    questions: dict  # tag -> count
    mode: str = "tags"  # "tags" or "hard_filter"
    hard_tags: Optional[List[str]] = None
    questions_count: Optional[int] = None


class EgeConvertingUpdate(BaseModel):
    data: dict  # input_mark -> output_mark


class TopicCreate(BaseModel):
    name: str
    volume: str


class TopicTagsUpdate(BaseModel):
    tags_list: List[str]


class BackupSettings(BaseModel):
    time: str     # "HH:MM" or ""
    chat_id: str  # Telegram chat ID


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="ChemBot Admin API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────────
# Auth routes
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/api/auth/login", response_model=LoginResponse)
def login(req: LoginRequest):
    if req.password != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Неверный пароль")
    token = create_token("admin")
    return {"token": token}


@app.get("/api/auth/verify")
def verify(token=Depends(require_auth)):
    return {"ok": True}


# ──────────────────────────────────────────────────────────────────────────────
# Image serving (public)
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/images/question/{question_id}")
def get_question_image(question_id: int):
    path = os.path.join(ROOT_FOLDER, "data", "questions_images", f"{question_id}.png")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/png")


@app.get("/api/images/answer/{question_id}")
def get_answer_image(question_id: int):
    path = os.path.join(ROOT_FOLDER, "data", "answers_images", f"{question_id}.png")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/png")


@app.get("/api/images/user/{telegram_id}")
def get_user_photo(telegram_id: int):
    path = os.path.join(ROOT_FOLDER, "data", "users_photos", f"{telegram_id}.jpg")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(path, media_type="image/jpeg")


# ──────────────────────────────────────────────────────────────────────────────
# Users (admin)
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/admin/users")
def list_users(_=Depends(require_auth)):
    users = get_all_users()
    return [
        {"id": u.id, "telegram_id": u.telegram_id, "name": u.name}
        for u in sorted(users, key=lambda u: u.name)
    ]


@app.delete("/api/admin/users/{telegram_id}")
def delete_user(telegram_id: int, _=Depends(require_auth)):
    remove_user(telegram_id=telegram_id)
    return {"ok": True}


@app.get("/api/admin/users/{telegram_id}/stats")
def user_stats(telegram_id: int, _=Depends(require_auth)):
    stats = get_user_statistics(telegram_id)
    result = []
    for s in stats:
        result.append({
            "work_id": s["general"]["work_id"],
            "name": s["general"]["name"],
            "type": s["general"]["type"],
            "start": s["general"]["time"]["start"].isoformat() if s["general"]["time"]["start"] else None,
            "end": s["general"]["time"]["end"].isoformat() if s["general"]["time"]["end"] else None,
            "final_mark": s["results"]["final_mark"],
            "max_mark": s["results"]["max_mark"],
            "fully": len(s["questions"]["fully"]),
            "semi": len(s["questions"]["semi"]),
            "zero": len(s["questions"]["zero"]),
            "questions_amount": s["general"].get("questions_amount", 0),
        })
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Student view (public – validated by url params)
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/student/work-stats")
def student_work_stats(uuid: str, tid: str, work: str, detailed: int = 0):
    work_obj = get_work_by_url_data(uuid, tid, work)
    if not work_obj:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    all_stats = get_user_statistics(int(tid))
    work_stats_list = [s for s in all_stats if s["general"]["work_id"] == int(work)]
    if not work_stats_list:
        raise HTTPException(status_code=404, detail="Статистика не найдена")

    ws = work_stats_list[-1]
    questions_list = get_work_questions_joined_pool(int(work))

    questions_data = []
    for idx, q in enumerate(questions_list):
        questions_data.append({
            "index": idx + 1,
            "question_id": q.question_id,
            "text": q.text,
            "answer": q.answer,
            "user_answer": q.user_answer,
            "user_mark": q.user_mark,
            "full_mark": q.full_mark,
            "question_image": bool(q.question_image),
            "answer_image": bool(q.answer_image),
        })

    user = ws["general"]["user"]
    return {
        "general": {
            "user_name": user.name if detailed else None,
            "name": ws["general"]["name"],
            "start": ws["general"]["time"]["start"].isoformat() if ws["general"]["time"]["start"] else None,
            "end": ws["general"]["time"]["end"].isoformat() if ws["general"]["time"]["end"] else None,
            "final_mark": ws["results"]["final_mark"],
            "max_mark": ws["results"]["max_mark"],
            "fully": len(ws["questions"]["fully"]),
            "semi": len(ws["questions"]["semi"]),
            "zero": len(ws["questions"]["zero"]),
        },
        "questions": questions_data,
        "detailed": bool(detailed),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Topics
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/admin/topics")
def list_topics(_=Depends(require_auth)):
    topics = get_topics_table()
    pool = get_all_pool(active=True)

    # count questions per tag
    tag_counter: dict = {}
    for q in pool:
        for tag in q.tags_list:
            tag_counter[tag] = tag_counter.get(tag, 0) + 1

    result: dict = {}
    for t in topics:
        if t.volume not in result:
            result[t.volume] = []
        result[t.volume].append({
            "id": t.id,
            "name": t.name,
            "tags": [
                {"tag": tag, "count": tag_counter.get(tag, 0)}
                for tag in sorted(t.tags_list)
            ],
        })

    return result


@app.post("/api/admin/topics")
def create_topic_endpoint(req: TopicCreate, _=Depends(require_auth)):
    t = create_topic(req.name, req.volume)
    return {"id": t.id, "name": t.name, "volume": t.volume, "tags": []}


@app.delete("/api/admin/topics/{topic_id}")
def delete_topic_endpoint(topic_id: int, _=Depends(require_auth)):
    deactivate_topic(topic_id)
    return {"ok": True}


@app.put("/api/admin/topics/{topic_id}")
def update_topic_endpoint(topic_id: int, req: TopicTagsUpdate, _=Depends(require_auth)):
    update_topic(topic_id, req.tags_list)
    return {"ok": True}


# ──────────────────────────────────────────────────────────────────────────────
# Hand works (create training)
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/api/admin/hand-works")
def create_hand_work(req: HandWorkCreate, _=Depends(require_auth)):
    all_questions = get_all_questions()

    if req.mode == "hard_filter":
        if not req.hard_tags or not req.questions_count:
            raise HTTPException(status_code=400, detail="Укажите теги и количество вопросов")
        result = get_random_questions_for_hard_tags_filter(
            pool=all_questions,
            tags_list=req.hard_tags,
            questions_count=req.questions_count,
        )
    else:
        if not req.questions:
            raise HTTPException(status_code=400, detail="Добавьте хотя бы один вопрос")
        result = get_random_questions(pool=all_questions, request_dict=req.questions)

    if not result["is_ok"]:
        raise HTTPException(status_code=400, detail=f"Недостаточно вопросов: {result.get('tag', '')}")

    identificator = hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:6]
    name = req.name or f"Тренировка {datetime.now().strftime('%Y%m%d%H%M')}"
    work = insert_new_hand_work(name=name, identificator=identificator, questions_ids_list=result["detail"])

    bot_token = os.getenv("BOT_API_KEY")
    bot_name = os.getenv("BOT_NAME")
    admin_id = os.getenv("ADMIN_ID")
    if bot_token and admin_id:
        try:
            bot = telebot.TeleBot(token=bot_token, parse_mode="html")
            bot.send_message(
                chat_id=admin_id,
                text=(
                    f"<b>ℹ️ Сервисные сообщения</b>\n\n"
                    f"Вы создали новую персональную тренировку. Отправьте ссылку на неё ученику.\n\n"
                    f"<b>{work.name}</b>\n"
                    f"https://t.me/{bot_name}?start=work_{work.identificator}"
                ),
            )
        except Exception:
            pass

    return {
        "id": work.id,
        "name": work.name,
        "identificator": work.identificator,
        "link": f"https://t.me/{bot_name}?start=work_{work.identificator}" if bot_name else None,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Question pool
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/admin/pool")
def list_pool(_=Depends(require_auth)):
    pool = get_all_pool(active=True)
    return [{"id": q.id, "text": q.text, "tags_list": q.tags_list} for q in pool]


@app.get("/api/admin/pool/template")
def get_pool_template(_=Depends(require_auth)):
    filepath = os.path.join(ROOT_FOLDER, "data", "excel_templates", "chembot_pool_list.xlsx")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="chembot_pool_list.xlsx",
    )


@app.post("/api/admin/pool/import")
def import_pool_excel(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    _=Depends(require_auth),
):
    filepath = os.path.join(
        ROOT_FOLDER, "data", "temp",
        f"pool_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx",
    )
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(file.file.read())

    import_data = import_pool(filepath)

    if not import_data["is_ok"]:
        clear_folder(os.path.join(ROOT_FOLDER, "data", "temp"))
        raise HTTPException(status_code=400, detail=import_data["comment"])

    if import_data["errors"]:
        clear_folder(os.path.join(ROOT_FOLDER, "data", "temp"))
        error_rows = " ".join(str(r) for r in import_data["errors"])
        raise HTTPException(
            status_code=400,
            detail=f"Ошибки в строках: {error_rows}. Исправьте и повторите загрузку.",
        )

    pool = insert_pool_data(import_data["data"])

    for el in pool:
        if bool(el.question_image):
            src = os.path.join(ROOT_FOLDER, "data", "temp", f"q_{el.import_id}.png")
            if os.path.exists(src):
                move_image(src, os.path.join(ROOT_FOLDER, "data", "questions_images", f"{el.id}.png"))
        if bool(el.answer_image):
            src = os.path.join(ROOT_FOLDER, "data", "temp", f"a_{el.import_id}.png")
            if os.path.exists(src):
                move_image(src, os.path.join(ROOT_FOLDER, "data", "answers_images", f"{el.id}.png"))

    background_tasks.add_task(clear_folder, os.path.join(ROOT_FOLDER, "data", "temp"))

    return {
        "ok": True,
        "imported_count": len(import_data["data"]),
        "message": f"Вопросы успешно импортированы ({len(import_data['data'])})",
    }


@app.get("/api/admin/pool/{question_id}")
def get_pool_question(question_id: int, _=Depends(require_auth)):
    q = get_question_from_pool(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    return {
        "id": q.id,
        "text": q.text,
        "answer": q.answer,
        "level": q.level,
        "full_mark": q.full_mark,
        "tags_list": q.tags_list,
        "is_rotate": q.is_rotate,
        "is_selfcheck": q.is_selfcheck,
        "question_image": bool(q.question_image),
        "answer_image": bool(q.answer_image),
        "type": q.type,
        "is_active": q.is_active,
    }


@app.put("/api/admin/pool/{question_id}")
def update_pool_question(question_id: int, data: QuestionUpdate, _=Depends(require_auth)):
    q = get_question_from_pool(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    q.text = data.text
    q.answer = data.answer
    q.level = data.level
    q.full_mark = data.full_mark
    q.tags_list = data.tags_list
    q.is_rotate = data.is_rotate
    q.is_selfcheck = data.is_selfcheck
    update_question(q)
    return {"ok": True}


@app.delete("/api/admin/pool/{question_id}")
def delete_pool_question(question_id: int, _=Depends(require_auth)):
    deactivate_question(question_id)
    return {"ok": True}


@app.post("/api/admin/pool")
def add_question(data: NewQuestion, _=Depends(require_auth)):
    pool = Pool(
        text=data.text,
        answer=data.answer,
        type=data.type,
        level=data.level,
        full_mark=data.full_mark,
        tags_list=data.tags_list,
        question_image=0,
        answer_image=0,
        is_selfcheck=int(data.is_selfcheck),
        is_rotate=int(data.is_rotate),
        created_at=datetime.now(),
        is_active=1,
    )
    q = insert_question_into_pool(pool)
    return {"id": q.id, "ok": True}


@app.post("/api/admin/pool/{question_id}/question-image")
def upload_question_image(question_id: int, file: UploadFile = File(...), _=Depends(require_auth)):
    dest = os.path.join(ROOT_FOLDER, "data", "questions_images", f"{question_id}.png")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(file.file.read())
    switch_image_flag(1, "question", question_id)
    return {"ok": True}


@app.delete("/api/admin/pool/{question_id}/question-image")
def remove_question_image(question_id: int, _=Depends(require_auth)):
    old = os.path.join(ROOT_FOLDER, "data", "questions_images", f"{question_id}.png")
    if os.path.exists(old):
        new_path = os.path.join(ROOT_FOLDER, "data", "questions_images",
                                f"removed_{datetime.now().timestamp()}_{question_id}.png")
        os.rename(old, new_path)
    switch_image_flag(0, "question", question_id)
    return {"ok": True}


@app.post("/api/admin/pool/{question_id}/answer-image")
def upload_answer_image(question_id: int, file: UploadFile = File(...), _=Depends(require_auth)):
    dest = os.path.join(ROOT_FOLDER, "data", "answers_images", f"{question_id}.png")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(file.file.read())
    switch_image_flag(1, "answer", question_id)
    return {"ok": True}


@app.delete("/api/admin/pool/{question_id}/answer-image")
def remove_answer_image(question_id: int, _=Depends(require_auth)):
    old = os.path.join(ROOT_FOLDER, "data", "answers_images", f"{question_id}.png")
    if os.path.exists(old):
        new_path = os.path.join(ROOT_FOLDER, "data", "answers_images",
                                f"removed_{datetime.now().timestamp()}_{question_id}.png")
        os.rename(old, new_path)
    switch_image_flag(0, "answer", question_id)
    return {"ok": True}


# ──────────────────────────────────────────────────────────────────────────────
# Topics Excel import/export
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/admin/topics/export")
def export_topics_excel(_=Depends(require_auth)):
    topics_list = get_all_topics(active=True)
    export_topics_list(topics_list)
    filepath = os.path.join(ROOT_FOLDER, "data", "temp", "chembot_topics_list.xlsx")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="chembot_topics_list.xlsx",
    )


@app.post("/api/admin/topics/import")
def import_topics_excel(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    _=Depends(require_auth),
):
    filepath = os.path.join(
        ROOT_FOLDER, "data", "temp",
        f"topics_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx",
    )
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(file.file.read())

    import_data = import_topics_list(filepath)

    if not import_data["is_ok"]:
        clear_folder(os.path.join(ROOT_FOLDER, "data", "temp"))
        raise HTTPException(status_code=400, detail=import_data["comment"])

    insert_topics_data(import_data["data"])
    background_tasks.add_task(clear_folder, os.path.join(ROOT_FOLDER, "data", "temp"))

    return {"ok": True, "message": import_data["comment"]}


# ──────────────────────────────────────────────────────────────────────────────
# EGE converting
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/admin/ege-converting")
def ege_converting(_=Depends(require_auth)):
    data = get_ege_converting()
    return [{"id": el.id, "input_mark": el.input_mark, "output_mark": el.output_mark} for el in data]


@app.put("/api/admin/ege-converting")
def update_ege(req: EgeConvertingUpdate, _=Depends(require_auth)):
    # req.data: {input_mark_str -> output_mark_int}
    config = {int(k): {"value": int(v), "is_ok": True} for k, v in req.data.items()}
    update_ege_converting(config)
    return {"ok": True}


# ──────────────────────────────────────────────────────────────────────────────
# Backup settings & on-demand backup
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/admin/backup-settings")
def get_backup_settings(_=Depends(require_auth)):
    return load_settings()


@app.post("/api/admin/backup-settings")
def update_backup_settings(req: BackupSettings, _=Depends(require_auth)):
    if req.time and len(req.time.split(":")) != 2:
        raise HTTPException(status_code=400, detail="Формат времени: HH:MM")
    settings = {"time": req.time.strip(), "chat_id": req.chat_id.strip()}
    save_settings(settings)
    _reschedule(settings["time"])
    return {"ok": True}


@app.post("/api/admin/backup-now")
def backup_now(_=Depends(require_auth)):
    result = _run_backup_job()
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "Ошибка"))
    return {"ok": True, "message": "Резервная копия отправлена"}


# ──────────────────────────────────────────────────────────────────────────────
# Backup restore
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/api/admin/restore")
def restore_backup(file: UploadFile = File(...), _=Depends(require_auth)):
    temp_dir = os.path.join(ROOT_FOLDER, "data", "temp",
                            f"restore_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        zip_path = os.path.join(temp_dir, "backup.zip")
        with open(zip_path, "wb") as f:
            f.write(file.file.read())

        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(temp_dir)

        # Restore database
        sql_files = glob_module.glob(os.path.join(temp_dir, "**", "*.sql"), recursive=True)
        if not sql_files:
            raise HTTPException(status_code=400, detail="SQL файл не найден в архиве")

        db_host = os.getenv("DB_HOST", "db")
        db_user = os.getenv("DB_USER", "chemistry")
        db_password = os.getenv("DB_PASSWORD", "")
        db_name = os.getenv("DB_NAME", "chemistry_bot")

        with open(sql_files[0], "rb") as sql_f:
            result = subprocess.run(
                ["mysql", f"-h{db_host}", f"-u{db_user}", f"-p{db_password}",
                 "--skip-ssl", db_name],
                stdin=sql_f,
                capture_output=True,
                timeout=300,
            )
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка восстановления БД: {result.stderr.decode(errors='replace')}",
            )

        # Restore images
        image_mapping = {
            "answers":   os.path.join(ROOT_FOLDER, "data", "answers_images"),
            "questions": os.path.join(ROOT_FOLDER, "data", "questions_images"),
            "users":     os.path.join(ROOT_FOLDER, "data", "users_photos"),
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

        return {"ok": True, "message": "Резервная копия успешно восстановлена"}

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ──────────────────────────────────────────────────────────────────────────────
# Serve React frontend (production)
# ──────────────────────────────────────────────────────────────────────────────
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
