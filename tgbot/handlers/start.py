import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, ReplyKeyboardRemove

from db.crud import (get_user, create_user)
from tgbot.handlers.menu import cmd_menu
from tgbot.lexicon.messages import lexicon
from tgbot.states.register_user import InputUserName

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    print(message.chat.id)
    user = get_user(message.from_user.id)
    if user is None:
        await state.set_state(InputUserName.waiting_for_msg)
        await message.answer(
            text=lexicon['start']['hello']
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
