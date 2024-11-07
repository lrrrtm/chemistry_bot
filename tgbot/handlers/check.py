from os import getenv

from aiogram import Router, types
from aiogram.filters import Command

from utils.services_checker import get_system_status

router = Router()


@router.message(Command("check"))
async def cmd_check(message: types.Message):
    if message.chat.id == int(getenv('ADMIN_ID')):
        data = get_system_status()
        text_to_send = ""
        for el in data:
            text_to_send += f"{el['status']}<b>{el['name']}</b>\n"

        await message.answer(
            text=f"<b>Состояние системы</b>\n\n{text_to_send}",
        )
