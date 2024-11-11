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
    today = time.localtime()
    today_date = time.strftime("%Y-%m-%d", today)

    # Check each file in the directory
    for filename in listdir(directory):
        file_path = path.join(directory, filename)
        file_creation_time = time.localtime(path.getctime(file_path))
        file_date = time.strftime("%Y-%m-%d", file_creation_time)

        if file_date == today_date:
            return filename

    return None

# Get directory path from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python3 backup_sender.py <dir>")
    sys.exit(1)

directory_path = sys.argv[1]

# Check if the file was created today
# data = check_file_created_today(directory_path)
if os.path.exists(directory_path):
    # Send the document to ADMIN and DEVELOPER
    with open(directory_path, "rb") as document:
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
