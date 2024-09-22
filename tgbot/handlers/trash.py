from os import getenv

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=getenv('BOT_API_KEY'), default=DefaultBotProperties(parse_mode='html'))