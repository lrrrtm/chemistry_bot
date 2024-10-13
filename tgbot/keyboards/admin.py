from os import getenv

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from db.models import User, Pool, WorkQuestion
from tgbot.lexicon.buttons import lexicon

from aiogram.filters.callback_data import CallbackData

from utils.services_checker import services


class AdminMenuBackCallbackFactory(CallbackData, prefix="admin_menu_back"):
    current_volume: str


class AdminMenuMainCallbackFactory(CallbackData, prefix="admin_menu_main"):
    volume: str


class AdminRebootServiceCallbackFactory(CallbackData, prefix="admin_reboot_service"):
    filename: str
    # name: str


def get_admin_menu_main_kb(auth_key: str, tid: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text=lexicon['admin']['create_topic_work'],
        callback_data=AdminMenuMainCallbackFactory(volume="create_topic_work"),
    )
    builder.button(
        text=lexicon['admin']['students_stats'],
        url=f"{getenv('STATS_HOST')}/stats?auth_key={auth_key}&admin_id={tid}"
    )
    builder.button(
        text=lexicon['admin']['system_status'],
        callback_data=AdminMenuMainCallbackFactory(volume="system_status"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_admin_system_status_kb(data: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for el in data:
        builder.button(
            text=el['name'],
            callback_data=f"service_{el['name']}"
        )
        builder.button(
            text=el['status'],
            callback_data=AdminRebootServiceCallbackFactory(filename=el['filename'])
        )
    builder.button(
        text=lexicon['service']['back'],
        callback_data=AdminMenuBackCallbackFactory(current_volume="system_status")
    )
    builder.adjust(2)
    return builder.as_markup()
