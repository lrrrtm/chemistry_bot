import subprocess
from os import getenv

from aiogram import Router, types
from aiogram.filters import Command

from tgbot.handlers.trash import bot

router = Router()

# Список сервисов, состояние которых вы хотите проверять
services = ['mysql.service', 'chemistry_stats.service', 'chemistry_bot.service']


async def check_services(message: types.Message):
    result = ""
    for service in services:
        try:
            status = subprocess.run(['systemctl', 'is-active', service], capture_output=True, text=True)
            service_status = status.stdout.strip()
            result += f"Сервис {service}: {service_status}\n"
        except Exception as e:
            result += f"Не удалось проверить статус {service}: {e}\n"

    await bot.send_message(
        chat_id=message.chat.id,
        text=f"Состояние сервисов:\n{result}",
    )

@router.message(Command("check"))
async def cmd_check(message: types.Message):
    if message.chat.id == int(getenv('FBACK_GROUP_ID')):
        await check_services(message)
