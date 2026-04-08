import hashlib
import os
from datetime import UTC, datetime

import telebot
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.dependencies import require_auth
from api.routers.hand_works.schemas import HandWorkCreate, SendTrainingRequest
from db.crud import (
    delete_hand_work,
    get_all_hand_works,
    get_all_questions,
    get_hand_work,
    get_hand_work_question_count,
    get_hand_work_questions,
    insert_new_hand_work,
)
from utils.mini_app_links import get_tma_share_link, get_tma_start_url, is_public_web_app_url
from utils.tags_helper import get_random_questions, get_random_questions_for_hard_tags_filter
from utils.work_pdf import build_work_pdf

router = APIRouter(prefix="/api/admin", tags=["hand_works"])
_ROOT_FOLDER = os.getenv("ROOT_FOLDER", os.path.abspath(os.getcwd()))


def _build_share_link(identificator: str) -> str | None:
    return get_tma_share_link(f"work_{identificator}")


def _build_start_url(identificator: str) -> str | None:
    return get_tma_start_url(f"work_{identificator}")


def _build_web_app_markup(identificator: str, button_text: str) -> telebot.types.InlineKeyboardMarkup | None:
    start_url = _build_start_url(identificator)
    markup = telebot.types.InlineKeyboardMarkup()
    if start_url and is_public_web_app_url(start_url):
        markup.add(
            telebot.types.InlineKeyboardButton(
                text=button_text,
                web_app=telebot.types.WebAppInfo(url=start_url),
            )
        )
        return markup

    share_link = _build_share_link(identificator)
    if share_link:
        markup.add(
            telebot.types.InlineKeyboardButton(
                text=button_text,
                url=share_link,
            )
        )
        return markup

    return None


@router.get("/hand-works")
def list_hand_works(_: str = Depends(require_auth)):
    works = get_all_hand_works()
    return [
        {
            "id": work.id,
            "name": work.name,
            "identificator": work.identificator,
            "created_at": work.created_at.isoformat(),
            "questions_count": get_hand_work_question_count(work.identificator),
            "link": _build_share_link(work.identificator),
            "web_link": _build_start_url(work.identificator),
        }
        for work in works
    ]


@router.delete("/hand-works/{work_id}")
def remove_hand_work(work_id: int, _: str = Depends(require_auth)):
    ok = delete_hand_work(work_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    return {"ok": True}


@router.post("/hand-works")
def create_hand_work(req: HandWorkCreate, _: str = Depends(require_auth)):
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
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно вопросов: {result.get('tag', '')}",
        )

    identificator = hashlib.sha256(str(datetime.now(UTC)).encode()).hexdigest()[:6]
    name = req.name or f"Тренировка {datetime.now().strftime('%Y%m%d%H%M')}"
    work = insert_new_hand_work(
        name=name,
        identificator=identificator,
        questions_ids_list=result["detail"],
    )

    bot_token = os.getenv("BOT_API_KEY")
    admin_id = os.getenv("ADMIN_ID")
    # if bot_token and admin_id:
    #     try:
    #         bot = telebot.TeleBot(token=bot_token, parse_mode="HTML")
    #         share_link = _build_share_link(work.identificator)
    #         bot.send_message(
    #             chat_id=admin_id,
    #             text=(
    #                 "<b>№️ Сервисные сообщения</b>\n\n"
    #                 "Вы создали новую персональную тренировку.\n\n"
    #                 f"<b>{work.name}</b>\n"
    #                 f"{share_link or 'Ссылка недоступна: проверьте настройки DOMAIN/BOT_NAME.'}"
    #             ),
    #             reply_markup=_build_web_app_markup(work.identificator, "Открыть в Mini App"),
    #         )
    #     except Exception:
    #         pass

    return {
        "id": work.id,
        "name": work.name,
        "identificator": work.identificator,
        "link": _build_share_link(work.identificator),
        "web_link": _build_start_url(work.identificator),
    }


@router.post("/send-training")
def send_training_to_user(req: SendTrainingRequest, _: str = Depends(require_auth)):
    bot_token = os.getenv("BOT_API_KEY")
    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_API_KEY не настроен")

    try:
        bot = telebot.TeleBot(token=bot_token, parse_mode="HTML")
        bot.send_message(
            chat_id=req.telegram_id,
            text=(
                "📝 <b>Новая тренировка</b>\n\n"
                f"<b>{req.name}</b>\n\n"
                "Преподаватель отправил тебе персональную тренировку. Чтобы начать, нажми на кнопку под сообщением"
            ),
            reply_markup=_build_web_app_markup(req.identificator, "Открыть тренировку"),
        )
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Ошибка отправки: {str(error)}") from error

    return {"ok": True}


@router.get("/hand-works/{identificator}/pdf")
def download_hand_work_pdf(identificator: str, _: str = Depends(require_auth)):
    hand_work = get_hand_work(identificator)
    if hand_work is None or getattr(hand_work, "is_deleted", 0):
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    questions = get_hand_work_questions(identificator)
    if not questions:
        raise HTTPException(status_code=404, detail="В тренировке нет вопросов")

    pdf_path, visible_name = build_work_pdf(
        root_folder=_ROOT_FOLDER,
        work_id=hand_work.id,
        work_title=hand_work.name,
        work_type_label="Работа от преподавателя",
        questions=questions,
    )

    return FileResponse(pdf_path, media_type="application/pdf", filename=visible_name)
