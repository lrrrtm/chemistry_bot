import os.path
from os import getenv, listdir, path
from dotenv import load_dotenv
import telebot
import time
import sys

# Load environment variables
load_dotenv()

# Initialize bot with API token
bot = telebot.TeleBot(token=getenv('BOT_API_KEY'), parse_mode="html")


def check_file_created_today(directory):
    res = None
    today = time.localtime()
    today_date = time.strftime("%Y-%m-%d", today)

    # Check each file in the directory
    for filename in listdir(directory):
        file_path = path.join(directory, filename)
        file_creation_time = time.localtime(path.getctime(file_path))
        file_date = time.strftime("%Y-%m-%d", file_creation_time)

        if file_date == today_date:
            res = filename

    return res

data = check_file_created_today('/root/backups')

if data is not None:
    with open(os.path.join('/root/backups', data), "rb") as document:
        bot.send_document(
            chat_id=getenv('ADMIN_ID'),
            document=document,
            caption="<b>ℹ️ Сервисные сообщения</b>\n\nРезервная копия базы данных"
        )
        bot.send_document(
            chat_id=getenv('DEVELOPER_ID'),
            document=document,
            caption="<b>ℹ️ Сервисные сообщения</b>\n\nРезервная копия базы данных"
        )
else:
    # Send a message if no backup file is found
    bot.send_message(
        chat_id=getenv('ADMIN_ID'),
        text="<b>ℹ️ Сервисные сообщения</b>\n\nРезервная копия базы данных не обнаружена, обратитесь к администратору"
    )
    bot.send_message(
        chat_id=getenv('DEVELOPER_ID'),
        text="<b>ℹ️ Сервисные сообщения</b>\n\nРезервная копия базы данных не обнаружена, обратитесь к администратору"
    )
