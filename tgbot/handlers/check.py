import subprocess
from os import getenv

from aiogram import Router, types
from aiogram.filters import Command

from tgbot.handlers.trash import bot

router = Router()

services = [
    {
        'name': "База данных",
        'filename': "mysql.service"
    },
    {
        'name': "Telegram-бот",
        'filename': "mysql.service"
    },
    {
        'name': "Панель статистики",
        'filename': "mysql.service"
    }
]

service_status_translation = {
    "active": "работает",
    "inactive": "остановлен",
    "failed": "завершён с ошибкой",
    "activating": "активируется",
    "deactivating": "останавливается",
    "reloading": "перезагружается",
    "unknown": "неизвестное состояние"
}



async def check_services(message: types.Message):
    result = ""
    for service in services:
        try:
            status = subprocess.run(['systemctl', 'is-active', service['filename']], capture_output=True, text=True)
            service_status = status.stdout.strip()
            result += f"<b>{service['name']}:</b> {service_status_translation[service_status]}\n"
        except Exception as e:
            result += f"{service['filename']}: {e}\n"

    await bot.send_message(
        chat_id=message.chat.id,
        text=f"Состояние сервисов:\n{result}",
    )


@router.message(Command("check"))
async def cmd_check(message: types.Message):
    if message.chat.id == int(getenv('FBACK_GROUP_ID')):
        await check_services(message)
