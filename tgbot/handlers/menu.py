from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from db.crud import (get_user)
from tgbot.keyboards.menu import get_menu_kb
from tgbot.lexicon.messages import lexicon

router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()

    user = get_user(message.from_user.id)
    if user is None:
        await message.answer(
            text="Для того, чтобы использовать эту команду, необходимо зарегистрироваться. Напиши или нажми /start"
        )
    else:
        await message.answer(
            text=lexicon['menu']['answers']['main_menu'],
            reply_markup=get_menu_kb()
        )


