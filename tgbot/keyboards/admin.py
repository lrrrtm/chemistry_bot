from os import getenv

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from tgbot.lexicon.buttons import lexicon

from aiogram.filters.callback_data import CallbackData


class AdminMenuBackCallbackFactory(CallbackData, prefix="admin_menu_back"):
    current_volume: str


class AdminMenuMainCallbackFactory(CallbackData, prefix="admin_menu_main"):
    volume: str


class AdminRebootServiceCallbackFactory(CallbackData, prefix="admin_reboot_service"):
    filename: str


def get_admin_menu_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    domain = getenv('DOMAIN', '')

    if domain:
        builder.button(
            text="🌐 Открыть панель управления",
            url=f"https://{domain}/admin"
        )
    builder.button(
        text=lexicon['admin']['database'],
        callback_data=AdminMenuMainCallbackFactory(volume="database"),
    )
    builder.button(
        text=lexicon['admin']['sender'],
        callback_data=AdminMenuMainCallbackFactory(volume="sender"),
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


def get_admin_db_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    domain = getenv('DOMAIN', '')

    builder.button(
        text=lexicon['admin']['update_topics_list'],
        callback_data=AdminMenuMainCallbackFactory(volume="update_topics_list")
    )
    builder.button(
        text=lexicon['admin']['update_pool'],
        callback_data=AdminMenuMainCallbackFactory(volume="pool_menu")
    )
    builder.button(
        text=lexicon['admin']['ege_converting'],
        url=f"https://{domain}/admin/ege-converting"
    )
    builder.button(
        text=lexicon['service']['back'],
        callback_data=AdminMenuBackCallbackFactory(current_volume="database")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_admin_pool_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    domain = getenv('DOMAIN', '')

    builder.button(
        text=lexicon['admin']['insert_pool'],
        callback_data=AdminMenuMainCallbackFactory(volume="insert_pool")
    )
    builder.button(
        text=lexicon['admin']['insert_pool_flet'],
        url=f"https://{domain}/admin/add-question"
    )
    builder.button(
        text=lexicon['admin']['edit_pool'],
        url=f"https://{domain}/admin/pool"
    )
    builder.button(
        text=lexicon['service']['back'],
        callback_data=AdminMenuBackCallbackFactory(current_volume="pool_menu")
    )

    builder.adjust(1)
    return builder.as_markup()

def get_admin_sender_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Подтверждаю, отправить",
        callback_data=AdminMenuMainCallbackFactory(volume="accept_sender")
    )
    builder.button(
        text="❌ Отменить рассылку",
        callback_data=AdminMenuMainCallbackFactory(volume="decline_sender")
    )

    builder.adjust(1)
    return builder.as_markup()

def get_admin_cancel_upload_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.button(
        text=lexicon['admin']['cancel_uploading_table']
    )

    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
