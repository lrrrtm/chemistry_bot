import asyncio
import logging
from os import getenv

from config import bot, dp
from threading import Thread

from tgbot.lexicon.messages import lexicon

logging.basicConfig(level=logging.INFO)

async def on_startup():
    await bot.send_message(
        chat_id=getenv('FBACK_GROUP_ID'),
        text=lexicon['service']['after_reboot']
    )

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await on_startup()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
