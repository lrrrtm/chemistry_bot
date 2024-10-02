from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from handlers import (start, help, feedback, menu, statistics, new_work, check)

load_dotenv()

bot = Bot(token=getenv('BOT_API_KEY'), default=DefaultBotProperties(parse_mode='html'))
dp = Dispatcher()

dp.include_routers(
    feedback.router,
    start.router,
    help.router,
    menu.router,
    statistics.router,
    new_work.router,
    check.router,
)
