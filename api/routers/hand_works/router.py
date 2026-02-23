import hashlib
import os
from datetime import datetime

import telebot
from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import require_auth
from api.routers.hand_works.schemas import HandWorkCreate, SendTrainingRequest
from db.crud import delete_hand_work, get_all_hand_works, get_all_questions, insert_new_hand_work
from utils.tags_helper import get_random_questions, get_random_questions_for_hard_tags_filter

router = APIRouter(prefix="/api/admin", tags=["hand_works"])


@router.get("/hand-works")
def list_hand_works(_: str = Depends(require_auth)):
    bot_name = os.getenv("BOT_NAME")
    works = get_all_hand_works()
    return [
        {
            "id": w.id,
            "name": w.name,
            "identificator": w.identificator,
            "created_at": w.created_at.isoformat(),
            "questions_count": len(w.questions_list),
            "link": f"https://t.me/{bot_name}?start=work_{w.identificator}"
            if bot_name
            else None,
        }
        for w in works
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
            raise HTTPException(
                status_code=400, detail="Укажите теги и количество вопросов"
            )
        result = get_random_questions_for_hard_tags_filter(
            pool=all_questions,
            tags_list=req.hard_tags,
            questions_count=req.questions_count,
        )
    else:
        if not req.questions:
            raise HTTPException(
                status_code=400, detail="Добавьте хотя бы один вопрос"
            )
        result = get_random_questions(pool=all_questions, request_dict=req.questions)

    if not result["is_ok"]:
        raise HTTPException(
            status_code=400,
            detail=f"Недостаточно вопросов: {result.get('tag', '')}",
        )

    identificator = hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:6]
    name = req.name or f"Тренировка {datetime.now().strftime('%Y%m%d%H%M')}"
    work = insert_new_hand_work(
        name=name,
        identificator=identificator,
        questions_ids_list=result["detail"],
    )

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
        "link": f"https://t.me/{bot_name}?start=work_{work.identificator}"
        if bot_name
        else None,
    }


@router.post("/send-training")
def send_training_to_user(req: SendTrainingRequest, _: str = Depends(require_auth)):
    bot_token = os.getenv("BOT_API_KEY")
    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_API_KEY не настроен")
    try:
        bot = telebot.TeleBot(token=bot_token, parse_mode="html")
        bot.send_message(
            chat_id=req.telegram_id,
            text=(
                f"📝 <b>Новая тренировка</b>\n\n"
                f"<b>{req.name}</b>\n\n"
                f"Преподаватель отправил тебе тренировку. Нажми на ссылку, чтобы начать:\n"
                f"{req.link}"
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка отправки: {str(e)}")
    return {"ok": True}
