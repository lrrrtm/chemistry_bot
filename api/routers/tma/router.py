"""
TMA (Telegram Mini App) router.

Supports two auth modes:
- Telegram Mini App auth via initData
- Web auth for invited students via X-Student-Token
"""

import html
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime
from typing import Optional
from urllib.parse import parse_qs, unquote

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import FSInputFile
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.routers.student_auth.service import (
    ACCESS_GRANT_PURPOSE_SELF_WEB_ACCESS,
    generate_one_time_token,
    hash_one_time_token,
    invite_expiration,
    verify_student_token,
)
from db.crud import (
    close_question,
    create_new_work,
    create_user,
    end_work,
    get_all_pool,
    get_all_topics,
    get_current_work_question,
    get_hand_work,
    get_hand_work_question_count,
    get_hand_work_questions,
    get_questions_list_by_id,
    get_session,
    get_skipped_questions,
    get_theory_document_by_id,
    get_theory_documents,
    get_topic_by_id,
    get_user,
    get_user_by_id,
    get_user_works_by_user_id,
    get_work_by_id,
    get_work_question_count,
    get_work_questions,
    get_work_questions_joined_pool,
    insert_work_questions,
    open_next_question,
    remove_work,
    requeue_skipped_questions,
    issue_student_access_grant,
    revoke_user_web_access,
    update_question_status,
)
from db.models import Pool, WorkQuestion
from utils.answer_checker import check_answer
from utils.mini_app_links import get_tma_invite_url, get_tma_start_url
from utils.tags_helper import get_ege_tags_list, get_questions_list_for_topic_work, get_random_questions
from utils.user_statistics import get_user_statistics_by_user_id
from utils.work_pdf import build_work_pdf

router = APIRouter(prefix="/api/tma", tags=["tma"])

_BOT_TOKEN = os.getenv("BOT_API_KEY", "")
_BOT_NAME = (os.getenv("BOT_NAME", "") or "").lstrip("@")
_ROOT_FOLDER = os.getenv("ROOT_FOLDER", ".")
_THEORY_DIR = os.path.join(_ROOT_FOLDER, "data", "theory_documents")
_BOT = Bot(token=_BOT_TOKEN, default=DefaultBotProperties(parse_mode="html")) if _BOT_TOKEN else None
_LOGGER = logging.getLogger(__name__)


class StudentContext(BaseModel):
    auth_mode: str
    telegram_id: int | None = None
    user_id: int | None = None


def _verify_init_data(init_data: str) -> bool:
    if not _BOT_TOKEN or not init_data:
        return False
    try:
        params = parse_qs(init_data, keep_blank_values=True)
        check_hash = params.get("hash", [None])[0]
        if not check_hash:
            return False
        data_check_string = "\n".join(f"{key}={value[0]}" for key, value in sorted(params.items()) if key != "hash")
        secret_key = hmac.new(b"WebAppData", _BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, check_hash)
    except Exception:
        return False


def _parse_telegram_id(init_data: str) -> Optional[int]:
    try:
        params = parse_qs(init_data, keep_blank_values=True)
        user_json = params.get("user", [None])[0]
        if not user_json:
            return None
        user = json.loads(unquote(user_json))
        return int(user["id"])
    except Exception:
        return None


def get_student_context(
    x_telegram_init_data: Optional[str] = Header(None),
    x_student_token: Optional[str] = Header(None),
) -> StudentContext:
    if x_telegram_init_data:
        if _BOT_TOKEN and not _verify_init_data(x_telegram_init_data):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData signature")

        telegram_id = _parse_telegram_id(x_telegram_init_data)
        if telegram_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cannot parse telegram_id from initData")

        user = get_user(telegram_id)
        return StudentContext(
            auth_mode="telegram",
            telegram_id=telegram_id,
            user_id=user.id if user else None,
        )

    if x_student_token:
        token_data = verify_student_token(x_student_token)
        if token_data is not None:
            user_id, token_version = token_data
            user = get_user_by_id(user_id)
            if user and (user.student_token_version or 0) == token_version:
                return StudentContext(
                    auth_mode="web",
                    telegram_id=user.telegram_id,
                    user_id=user.id,
                )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth")


def _require_user(context: StudentContext):
    if context.user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered")
    user = get_user_by_id(context.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered")
    return user


def _serialize_me(context: StudentContext, user=None):
    if user is None:
        return {
            "registered": False,
            "auth_mode": context.auth_mode,
            "telegram_id": context.telegram_id,
            "telegram_linked": bool(context.telegram_id),
            "has_web_credentials": False,
        }

    return {
        "registered": True,
        "auth_mode": context.auth_mode,
        "telegram_id": user.telegram_id,
        "telegram_linked": bool(user.telegram_id),
        "has_web_credentials": bool(user.username and user.password_hash),
        "name": user.name,
        "username": user.username,
    }


def _require_work(work_id: int, user_id: int):
    work = get_work_by_id(work_id)
    if not work or work.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work not found")
    return work


def _build_advance_response(work_id: int):
    next_question = open_next_question(work_id)

    if next_question is None:
        skipped = get_skipped_questions(work_id)
        if skipped:
            return {"type": "skipped", "count": len(skipped)}
        end_work(work_id)
        return {"type": "complete"}

    row = get_current_work_question(work_id)
    total = get_work_question_count(work_id)
    return {
        "type": "question",
        "question": _row_to_question(row, total),
    }


def _row_to_question(row, total: int) -> dict:
    return {
        "work_question_id": row.id,
        "position": row.position,
        "total": total,
        "question_id": row.question_id,
        "text": row.text,
        "question_image": bool(row.question_image),
        "is_selfcheck": bool(row.is_selfcheck),
        "full_mark": row.full_mark,
        "answer": None,
        "answer_image": bool(row.answer_image),
    }


def _resolve_work_title(work_type: str, topic_id: Optional[int], hand_work_id: Optional[str]) -> tuple[str, str]:
    if work_type == "ege":
        return "КИМ ЕГЭ", "Тренировка в формате ЕГЭ"

    if work_type == "topic":
        topic = get_topic_by_id(topic_id) if topic_id else None
        topic_name = topic.name if topic else "Персональная тренировка"
        return topic_name, "Персональная тренировка"

    hand_work = get_hand_work(hand_work_id) if hand_work_id else None
    hand_work_name = hand_work.name if hand_work else "Работа от преподавателя"
    return hand_work_name, "Работа от преподавателя"


async def _send_work_pdf_to_chat(
    *,
    chat_id: int,
    work_id: int,
    work_title: str,
    work_type_label: str,
    questions_list: list[Pool],
):
    if _BOT is None:
        _LOGGER.warning("Skipping work PDF send for work_id=%s: bot is not configured", work_id)
        return

    try:
        pdf_path, visible_name = build_work_pdf(
            root_folder=_ROOT_FOLDER,
            work_id=work_id,
            work_title=work_title,
            work_type_label=work_type_label,
            questions=questions_list,
        )
        await _BOT.send_document(
            chat_id=chat_id,
            document=FSInputFile(pdf_path, filename=visible_name),
            caption=f"{html.escape(work_title)} в формате PDF",
        )
    except Exception:
        _LOGGER.exception("Failed to generate or send work PDF for work_id=%s", work_id)


class RegisterBody(BaseModel):
    name: str


class CreateWorkBody(BaseModel):
    work_type: str
    topic_id: Optional[int] = None
    hand_work_id: Optional[str] = None
    replace_active: bool = False
    pdf_delivery: str = "none"


class AnswerBody(BaseModel):
    work_question_id: int
    answer: str


class SelfCheckBody(BaseModel):
    work_question_id: int
    mark: int


class SkipBody(BaseModel):
    work_question_id: int


def _get_work_pdf_payload(work) -> tuple[str, str, list[Pool]]:
    work_title, work_type_label = _resolve_work_title(
        work_type=work.work_type,
        topic_id=work.topic_id,
        hand_work_id=work.hand_work_id,
    )
    question_ids = [question.question_id for question in get_work_questions(work.id)]
    questions_list = get_questions_list_by_id(question_ids)
    return work_title, work_type_label, questions_list


@router.get("/me")
def get_me(context: StudentContext = Depends(get_student_context)):
    if context.user_id is None:
        return _serialize_me(context)

    user = _require_user(context)
    return _serialize_me(context, user)


@router.post("/register")
def register(body: RegisterBody, context: StudentContext = Depends(get_student_context)):
    if context.auth_mode != "telegram" or context.telegram_id is None:
        raise HTTPException(status_code=400, detail="Регистрация по имени доступна только внутри Telegram")

    name = body.name.strip()
    if not name or len(name) > 30:
        raise HTTPException(status_code=400, detail="Имя должно быть от 1 до 30 символов")

    existing = get_user(context.telegram_id)
    if existing:
        return {
            "registered": True,
            "auth_mode": "telegram",
            "telegram_id": existing.telegram_id,
            "telegram_linked": True,
            "name": existing.name,
            "username": existing.username,
        }

    user = create_user(name=name, tid=context.telegram_id)
    return {
        "registered": True,
        "auth_mode": "telegram",
        "telegram_id": user.telegram_id,
        "telegram_linked": True,
        "name": user.name,
        "username": user.username,
    }


@router.get("/topics")
def list_topics(context: StudentContext = Depends(get_student_context)):
    _require_user(context)
    topics = get_all_topics(active=True)
    return [{"id": topic.id, "name": topic.name, "volume": topic.volume} for topic in topics]


@router.post("/profile/web-access/start")
def start_web_access_setup(context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)

    if user.username and user.password_hash:
        login_url = get_tma_start_url()
        if not login_url:
            raise HTTPException(status_code=503, detail="Веб-адрес приложения не настроен")
        return {
            "mode": "login",
            "url": login_url,
        }

    raw_token = generate_one_time_token()
    expires_at = invite_expiration()
    grant = issue_student_access_grant(
        user_id=user.id,
        purpose=ACCESS_GRANT_PURPOSE_SELF_WEB_ACCESS,
        token_hash=hash_one_time_token(raw_token),
        expires_at=expires_at,
        created_by="student_self_service",
    )
    if not grant:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    invite_url = get_tma_invite_url(raw_token)
    if not invite_url:
        raise HTTPException(status_code=503, detail="Веб-адрес приложения не настроен")

    return {
        "mode": "setup",
        "url": invite_url,
        "expires_at": expires_at.isoformat(),
    }


@router.delete("/profile/web-access")
def revoke_web_access(context: StudentContext = Depends(get_student_context)):
    if context.auth_mode != "telegram":
        raise HTTPException(status_code=400, detail="Отключить веб-доступ можно только из Telegram")

    user = _require_user(context)
    updated_user = revoke_user_web_access(user.id)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    return _serialize_me(context, updated_user)


@router.get("/theory-documents")
def list_theory_documents(query: str = "", context: StudentContext = Depends(get_student_context)):
    _require_user(context)
    documents = get_theory_documents(active=True, query=query)
    return [
        {
            "id": document.id,
            "title": document.title,
            "tags_list": document.tags_list,
            "file_size": document.file_size,
            "created_at": document.created_at.isoformat() if document.created_at else None,
        }
        for document in documents
    ]


@router.post("/theory-documents/{document_id}/send")
async def send_theory_document_to_chat(document_id: int, context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    if not user.telegram_id:
        raise HTTPException(
            status_code=409,
            detail="Сначала привяжите Telegram в профиле, чтобы получать документы в чат.",
        )

    document = get_theory_document_by_id(document_id, active_only=True)
    if not document:
        raise HTTPException(status_code=404, detail="Документ не найден")

    path = os.path.join(_THEORY_DIR, document.file_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Файл документа не найден")

    if _BOT is None:
        raise HTTPException(status_code=503, detail="Бот недоступен")

    visible_name = document.original_file_name or f"{document.title}.pdf"

    try:
        await _BOT.send_document(
            chat_id=user.telegram_id,
            document=FSInputFile(path, filename=visible_name),
            caption=f"Теория: <b>{html.escape(document.title)}</b>",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=409,
            detail="Не удалось отправить документ в чат. Откройте диалог с ботом и попробуйте снова.",
        ) from exc

    return {
        "ok": True,
        "chat_url": f"https://t.me/{_BOT_NAME}" if _BOT_NAME else "https://t.me",
    }


@router.get("/hand-works/{identificator}")
def get_hand_work_info(identificator: str, context: StudentContext = Depends(get_student_context)):
    _require_user(context)
    hand_work = get_hand_work(identificator)
    if not hand_work or hand_work.is_deleted:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    return {
        "name": hand_work.name,
        "identificator": hand_work.identificator,
        "questions_count": get_hand_work_question_count(identificator),
    }


@router.get("/works/active")
def get_active_work(context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    works = get_user_works_by_user_id(user.id)
    if not works or works[0].end_datetime is not None:
        return None

    active = works[0]
    current_question = get_current_work_question(active.id)
    if current_question is None:
        recovered_question = open_next_question(active.id)
        if recovered_question is None:
            skipped = get_skipped_questions(active.id)
            if skipped:
                requeue_skipped_questions(active.id)
                recovered_question = open_next_question(active.id)

        if recovered_question is None:
            remove_work(active.id)
            return None

    questions = get_work_questions(active.id)
    answered = sum(1 for question in questions if question.status == "answered")
    return {
        "id": active.id,
        "work_type": active.work_type,
        "hand_work_id": active.hand_work_id,
        "topic_id": active.topic_id,
        "total": len(questions),
        "answered": answered,
    }


@router.delete("/works/active", status_code=204)
def abandon_active_work(context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    works = get_user_works_by_user_id(user.id)
    if works and works[0].end_datetime is None:
        remove_work(works[0].id)


@router.get("/works")
def list_works(context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    all_stats = get_user_statistics_by_user_id(user.id)
    result = []
    for work_stat in all_stats:
        general = work_stat["general"]
        result.append(
            {
                "id": general["work_id"],
                "work_type": general["type"],
                "name": general["name"],
                "final_mark": work_stat["results"]["final_mark"],
                "max_mark": work_stat["results"]["max_mark"],
                "fully": len(work_stat["questions"]["fully"]),
                "semi": len(work_stat["questions"]["semi"]),
                "zero": len(work_stat["questions"]["zero"]),
                "start_datetime": general["time"]["start"].isoformat() if general["time"]["start"] else None,
                "end_datetime": general["time"]["end"].isoformat() if general["time"]["end"] else None,
            }
        )
    return result


@router.post("/works")
async def create_work(
    body: CreateWorkBody,
    background_tasks: BackgroundTasks,
    context: StudentContext = Depends(get_student_context),
):
    user = _require_user(context)

    existing = get_user_works_by_user_id(user.id)
    if existing and existing[0].end_datetime is None:
        if not body.replace_active:
            raise HTTPException(
                status_code=409,
                detail="У вас уже есть незавершённая тренировка. Подтвердите замену, чтобы начать новую.",
            )
        remove_work(existing[0].id)

    if body.work_type not in ("ege", "topic", "hand_work"):
        raise HTTPException(status_code=400, detail="Неверный тип работы")

    if body.pdf_delivery not in ("none", "telegram", "download"):
        raise HTTPException(status_code=400, detail="Invalid pdf_delivery")

    if body.work_type == "topic" and not body.topic_id:
        raise HTTPException(status_code=400, detail="Не указан topic_id")

    if body.work_type == "hand_work":
        if not body.hand_work_id:
            raise HTTPException(status_code=400, detail="Не указан hand_work_id")
        hand_work = get_hand_work(body.hand_work_id)
        if not hand_work or hand_work.is_deleted:
            raise HTTPException(status_code=404, detail="Работа от преподавателя не найдена")

    if body.pdf_delivery == "telegram" and (context.auth_mode != "telegram" or not user.telegram_id):
        raise HTTPException(status_code=409, detail="PDF can be sent to Telegram only from Telegram session")

    work = create_new_work(
        user_id=user.id,
        work_type=body.work_type,
        topic_id=body.topic_id,
        hand_work_id=body.hand_work_id,
    )

    if body.work_type == "ege":
        pool = get_all_pool(active=True)
        tags_list = get_ege_tags_list(each_question_limit=1)
        result = get_random_questions(pool=pool, request_dict=tags_list)
        if not result["is_ok"]:
            remove_work(work.id)
            raise HTTPException(status_code=500, detail="Не хватает вопросов для ЕГЭ-тренировки")
        questions_list = get_questions_list_by_id(result["detail"])
    elif body.work_type == "topic":
        result = get_questions_list_for_topic_work(topic_id=body.topic_id)
        if not result["is_ok"]:
            remove_work(work.id)
            raise HTTPException(status_code=500, detail="Не хватает вопросов по этой теме")
        questions_list = result["detail"]
    else:
        questions_list = get_hand_work_questions(body.hand_work_id)

    insert_work_questions(work, questions_list)
    open_next_question(work.id)

    if body.pdf_delivery == "telegram":
        if context.auth_mode != "telegram" or not user.telegram_id:
            raise HTTPException(status_code=409, detail="PDF can be sent to Telegram only from Telegram session")
        work_title, work_type_label = _resolve_work_title(
            work_type=body.work_type,
            topic_id=body.topic_id,
            hand_work_id=body.hand_work_id,
        )
        background_tasks.add_task(
            _send_work_pdf_to_chat,
            chat_id=user.telegram_id,
            work_id=work.id,
            work_title=work_title,
            work_type_label=work_type_label,
            questions_list=questions_list,
        )

    return {"work_id": work.id}


@router.get("/works/{work_id}/pdf")
def download_work_pdf(work_id: int, context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    work = _require_work(work_id, user.id)
    work_title, work_type_label, questions_list = _get_work_pdf_payload(work)
    pdf_path, visible_name = build_work_pdf(
        root_folder=_ROOT_FOLDER,
        work_id=work.id,
        work_title=work_title,
        work_type_label=work_type_label,
        questions=questions_list,
    )
    return FileResponse(pdf_path, media_type="application/pdf", filename=visible_name)


@router.get("/works/{work_id}/question")
def get_question(work_id: int, context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    _require_work(work_id, user.id)

    row = get_current_work_question(work_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Нет активного вопроса")

    total = get_work_question_count(work_id)
    return _row_to_question(row, total)


@router.post("/works/{work_id}/answer")
def submit_answer(work_id: int, body: AnswerBody, context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    _require_work(work_id, user.id)

    with get_session() as session:
        work_question = session.query(WorkQuestion).filter_by(id=body.work_question_id, work_id=work_id).first()
        if not work_question:
            raise HTTPException(status_code=404, detail="Вопрос не найден")
        pool_question = session.query(Pool).filter_by(id=work_question.question_id).first()

    if bool(pool_question.is_selfcheck):
        raise HTTPException(status_code=400, detail="Этот вопрос требует самопроверки")

    mark = check_answer(pool_question, body.answer.strip())
    close_question(
        q_id=body.work_question_id,
        user_answer=body.answer.strip(),
        user_mark=mark,
        end_datetime=datetime.now(),
    )
    return _build_advance_response(work_id)


@router.post("/works/{work_id}/self-check")
def submit_self_check(work_id: int, body: SelfCheckBody, context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    _require_work(work_id, user.id)

    with get_session() as session:
        work_question = session.query(WorkQuestion).filter_by(id=body.work_question_id, work_id=work_id).first()
        if not work_question:
            raise HTTPException(status_code=404, detail="Вопрос не найден")
        pool_question = session.query(Pool).filter_by(id=work_question.question_id).first()

    if body.mark < 0 or body.mark > pool_question.full_mark:
        raise HTTPException(status_code=400, detail=f"Балл должен быть от 0 до {pool_question.full_mark}")

    close_question(
        q_id=body.work_question_id,
        user_answer="самостоятельная проверка",
        user_mark=body.mark,
        end_datetime=datetime.now(),
    )
    return _build_advance_response(work_id)


@router.post("/works/{work_id}/skip")
def skip_question(work_id: int, body: SkipBody, context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    _require_work(work_id, user.id)

    with get_session() as session:
        work_question = session.query(WorkQuestion).filter_by(id=body.work_question_id, work_id=work_id).first()
        if not work_question:
            raise HTTPException(status_code=404, detail="Вопрос не найден")

    update_question_status(body.work_question_id, "skipped")
    return _build_advance_response(work_id)


@router.post("/works/{work_id}/requeue-skipped", status_code=204)
def requeue_skipped(work_id: int, context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    _require_work(work_id, user.id)
    requeue_skipped_questions(work_id)
    open_next_question(work_id)


@router.post("/works/{work_id}/finish")
def finish_work(work_id: int, context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    _require_work(work_id, user.id)

    skipped = get_skipped_questions(work_id)
    for question in skipped:
        close_question(
            q_id=question.id,
            user_answer="вопрос пропущен",
            user_mark=0,
            start_datetime=datetime.now(),
            end_datetime=datetime.now(),
        )
    end_work(work_id)
    return {"type": "complete"}


@router.get("/works/{work_id}/results")
def get_work_results(work_id: int, context: StudentContext = Depends(get_student_context)):
    user = _require_user(context)
    work = _require_work(work_id, user.id)

    if work.end_datetime is None:
        raise HTTPException(status_code=400, detail="Работа ещё не завершена")

    all_stats = get_user_statistics_by_user_id(user.id)
    stats_list = [stat for stat in all_stats if stat["general"]["work_id"] == work_id]
    if not stats_list:
        raise HTTPException(status_code=404, detail="Статистика не найдена")
    stats = stats_list[-1]

    questions_list = get_work_questions_joined_pool(work_id)
    questions_data = [
        {
            "index": index + 1,
            "question_id": question.question_id,
            "text": question.text,
            "answer": question.answer,
            "user_answer": question.user_answer,
            "user_mark": question.user_mark if question.user_mark is not None else 0,
            "full_mark": question.full_mark,
            "question_image": bool(question.question_image),
            "answer_image": bool(question.answer_image),
        }
        for index, question in enumerate(questions_list)
    ]

    general = stats["general"]
    return {
        "general": {
            "telegram_id": user.telegram_id,
            "user_name": user.name,
            "name": general["name"],
            "start": general["time"]["start"].isoformat() if general["time"]["start"] else None,
            "end": general["time"]["end"].isoformat() if general["time"]["end"] else None,
            "final_mark": stats["results"]["final_mark"],
            "max_mark": stats["results"]["max_mark"],
            "fully": len(stats["questions"]["fully"]),
            "semi": len(stats["questions"]["semi"]),
            "zero": len(stats["questions"]["zero"]),
        },
        "questions": questions_data,
    }
