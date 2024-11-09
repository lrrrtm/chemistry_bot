import asyncio
import logging
from os import getenv

from aiogram.types import ReplyKeyboardRemove

from config import bot, dp
from threading import Thread

from tgbot.lexicon.messages import lexicon
from utils.clearing import clear_folder

logging.basicConfig(level=logging.INFO)

async def on_startup():
    clear_folder(f"{getenv('ROOT_FOLDER')}/data/temp")
    await bot.send_message(
        chat_id=getenv('ADMIN_ID'),
        text=lexicon['service']['after_reboot'],
        reply_markup=ReplyKeyboardRemove()
    )
    await bot.send_message(
        chat_id=getenv('DEVELOPER_ID'),
        text=lexicon['service']['after_reboot'],
        reply_markup=ReplyKeyboardRemove()
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await on_startup()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
