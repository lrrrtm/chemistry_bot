from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from db.crud import (get_user, get_user_works, get_topic, get_work_questions)
from tgbot.keyboards.menu import get_menu_kb
from tgbot.lexicon.messages import lexicon
from tgbot.lexicon.buttons import lexicon as btns_lexicon

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


@router.message(F.text == btns_lexicon['main_menu']['stats'])
async def cmd_stats(message: Message, state: FSMContext):
    msg = await message.answer(
        text="Собираем твою статистику..."
    )

    works_list = get_user_works(message.from_user.id)
    works_list = works_list[::-1]

    if works_list:
        await message.answer(
            text=f"works list finded"
        )

    else:
        await msg.delete()
        await message.answer(
            text=f"У тебя ещё ни одного завершённого задания, чтобы мы могли собрать статистику. \n\nНачни решать, нажав на кнопку <b>«{btns_lexicon['main_menu']['new_work']}»</b>"
        )
