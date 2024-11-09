from os import getenv, listdir, path
from dotenv import load_dotenv

import telebot
import time

load_dotenv()

bot = telebot.TeleBot(token=getenv('BOT_API_KEY'), parse_mode="html")


def check_file_created_today(directory):
    today = time.localtime()  # Текущая дата
    today_date = time.strftime("%Y-%m-%d", today)  # Форматируем как YYYY-MM-DD

    for filename in listdir(directory):
        file_path = path.join(directory, filename)

        # Получаем время последнего изменения файла
        file_creation_time = time.localtime(path.getctime(file_path))
        file_date = time.strftime("%Y-%m-%d", file_creation_time)

        if file_date == today_date:
            return filename

    return None


directory_path = "/root/backups"

data = check_file_created_today(directory_path)
if data is not None:
    bot.send_document(
        chat_id="409801981",
        document=open(path.join(directory_path, data), "rb"),
        caption="<b>ℹ️ Сервисные сообщения</b>\n\nРезервная копия базы данных"
    )
else:
    bot.send_message(
        chat_id="409801981",
        text="<b>ℹ️ Сервисные сообщения</b>\n\nРезервная копия базы данных не обнаружена, обратитесь к администратору"
    )