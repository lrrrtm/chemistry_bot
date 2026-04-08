import re
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from api.routers.student_auth.service import hash_one_time_token
from db.crud import create_user, get_hand_work, get_user, get_user_by_telegram_link_token_hash, link_telegram_to_user
from tgbot.handlers.trash import save_user_photo
from tgbot.keyboards.mini_app import get_open_mini_app_kb
from tgbot.lexicon.messages import lexicon
from tgbot.states.register_user import InputUserName

router = Router()


async def send_open_app_message(message: Message):
    await message.answer(
        text=(
            "Чтобы запустить приложение, нажми на кнопку под сообщением"
        ),
        reply_markup=get_open_mini_app_kb("Запустить приложение"),
    )


@router.message(CommandStart(deep_link=True, magic=F.args.regexp(re.compile(r"(link)_[-\w]+"))))
async def deep_link_telegram_link(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()

    raw_token = command.args.split("_", 1)[-1]
    user = get_user_by_telegram_link_token_hash(hash_one_time_token(raw_token))

    if not user or not user.telegram_link_token_hash:
        await message.answer("Ссылка для привязки Telegram недействительна или уже использована.")
        return

    if user.telegram_link_expires_at and user.telegram_link_expires_at < datetime.now():
        await message.answer("Срок действия ссылки для привязки уже истёк. Запроси новую в профиле.")
        return

    try:
        link_telegram_to_user(user.id, message.from_user.id)
    except ValueError:
        await message.answer("Этот Telegram-аккаунт уже привязан к другому ученику.")
        return

    await message.answer(
        text=(
            f"Telegram успешно привязан к профилю <b>{user.name}</b>.\n\n"
            "Теперь ты можешь открывать приложение прямо внутри Telegram."
        ),
        reply_markup=get_open_mini_app_kb("Открыть приложение"),
    )


@router.message(CommandStart(deep_link=True, magic=F.args.regexp(re.compile(r"(work)_\w+"))))
async def deep_linking(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()

    identificator = command.args.split("_")[-1]
    work = get_hand_work(identificator=identificator)

    if not work:
        await message.answer(
            text="Персональная тренировка с такой ссылкой не найдена. Проверь ссылку или обратись к преподавателю."
        )
        return

    await message.answer(
        text=(
            "<b>Новая тренировка от преподавателя</b>\n\n"
            f"<b>{work.name}</b>\n\n"
            "Открой мини-приложение кнопкой ниже. На первом экране ты увидишь эту тренировку и кнопку для старта."
        ),
        reply_markup=get_open_mini_app_kb(
            button_text="Открыть тренировку",
            startapp=f"work_{identificator}",
        ),
    )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)

    if user is None:
        await state.set_state(InputUserName.waiting_for_msg)
        await message.answer(
            text=lexicon["start"]["hello"],
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await send_open_app_message(message)


@router.message(InputUserName.waiting_for_msg)
async def register_user(message: Message, state: FSMContext):
    await state.clear()

    user_name = message.text.strip()
    if len(user_name) < 100:
        user_name = " ".join(el.capitalize() for el in user_name.split(" "))
        await save_user_photo(message)
        user = create_user(user_name, message.from_user.id)
        await message.answer(text=lexicon["start"]["reg_ok"].format(user.name))
        await send_open_app_message(message)
        return

    await state.set_state(InputUserName.waiting_for_msg)
    await message.answer(text=lexicon["start"]["bad_name"])
