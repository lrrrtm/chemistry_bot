import re

from aiogram import Router, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, ReplyKeyboardRemove

from db.crud import (get_user, create_user, get_hand_work)
from tgbot.handlers.menu import cmd_menu
from tgbot.keyboards.new_work import get_start_work_kb
from tgbot.lexicon.messages import lexicon
from tgbot.states.register_user import InputUserName

router = Router()


@router.message(CommandStart(deep_link=True, magic=F.args.regexp(re.compile(r'(work)_\w+'))))
async def deep_linking(message: Message, command: CommandObject, state: FSMContext):
    identificator = command.args.split("_")[-1]
    work = get_hand_work(identificator=identificator)

    if work:
        await message.answer(
            text=lexicon['new_work']['hand_work_caption'],
            reply_markup=get_start_work_kb(work_type="hand_work", hand_work_id=identificator)
        )
    else:
        await message.answer(
            text="Персональная тренировка с таким номером не найдена. Проверь правильность ссылки или обратись к преподавателю."
        )
        await cmd_menu(message, state)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)
    if user is None:
        await state.set_state(InputUserName.waiting_for_msg)
        await message.answer(
            text=lexicon['start']['hello'],
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await cmd_menu(message, state)


@router.message(InputUserName.waiting_for_msg)
async def register_user(message: Message, state: FSMContext):
    await state.clear()

    user_name = message.text.strip()
    if (
            len(user_name) <= 30 and
            len(re.findall(r'\w+', user_name)) == 1 and
            bool(re.match(r'^[A-Za-zА-Яа-яёЁ\s]+$', user_name))
    ):
        user = create_user(user_name, message.from_user.id)
        await message.answer(
            text=lexicon['start']['reg_ok'].format(user.name)
        )
    else:
        await state.set_state(InputUserName.waiting_for_msg)
        await message.answer(
            text=lexicon['start']['bad_name']
        )
