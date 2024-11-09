from os import getenv, listdir, path
from dotenv import load_dotenv

import telebot
import time

load_dotenv()

bot = telebot.TeleBot(token=getenv('BOT_API_KEY'), parse_mode="html")


def check_file_created_today(directory):
    today = time.localtime()
    today_date = time.strftime("%Y-%m-%d", today)

    for filename in listdir(directory):
        file_path = path.join(directory, filename)

        file_creation_time = time.localtime(path.getctime(file_path))
        file_date = time.strftime("%Y-%m-%d", file_creation_time)

        if file_date == today_date:
            return filename

    return None


directory_path = "/root/backups"

data = check_file_created_today(directory_path)
if data is not None:
    bot.send_document(
        chat_id=getenv('ADMIN_ID'),
        document=open(path.join(directory_path, data), "rb"),
        caption="<b>ℹ️ Сервисные сообщения</b>\n\nРезервная копия базы данных"
    )
    bot.send_document(
        chat_id=getenv('DEVELOPER_ID'),
        document=open(path.join(directory_path, data), "rb"),
        caption="<b>ℹ️ Сервисные сообщения</b>\n\nРезервная копия базы данных"
    )
else:
    bot.send_message(
        chat_id=getenv('ADMIN_ID'),
        text="<b>ℹ️ Сервисные сообщения</b>\n\nРезервная копия базы данных не обнаружена, обратитесь к администратору"
    )
    bot.send_message(
        chat_id=getenv('DEVELOPER_ID'),
        text="<b>ℹ️ Сервисные сообщения</b>\n\nРезервная копия базы данных не обнаружена, обратитесь к администратору"
    )