import os
from os import getenv

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()
bot = Bot(token=getenv('BOT_API_KEY'), default=DefaultBotProperties(parse_mode='html'))

async def save_user_photo(message: Message):
    user_id = message.from_user.id
    user_photos = await bot.get_user_profile_photos(user_id)

    if user_photos.total_count > 0:
        photo_file_id = user_photos.photos[0][-1].file_id

        file_info = await bot.get_file(photo_file_id)

        file_path = file_info.file_path
        destination = f"{os.getenv('ROOT_FOLDER')}/flet_apps/assets/users_photos/{message.from_user.id}.jpg"

        await bot.download_file(file_path, destination)