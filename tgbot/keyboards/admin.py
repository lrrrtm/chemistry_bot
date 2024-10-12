from os import getenv

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from db.models import User, Pool, WorkQuestion
from tgbot.lexicon.buttons import lexicon

from aiogram.filters.callback_data import CallbackData


class AdminMenuMainCallbackFactory(CallbackData, prefix="admin_menu_main"):
    volume: str


def get_admin_menu_main_kb(auth_key: str = 'developer') -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Создание тренировки",
        callback_data=AdminMenuMainCallbackFactory(volume="create_topic_work"),
    )
    builder.button(
        text="Статистика учеников",
        url=f"{getenv('STATS_HOST')}/stats?akey={auth_key}",
        # callback_data=AdminMenuMainCallbackFactory(volume="students_stats"),
    )
    builder.button(
        text="Состояние системы",
        callback_data=AdminMenuMainCallbackFactory(volume="system_status"),
    )
    builder.adjust(1)
    return builder.as_markup()
