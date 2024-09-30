from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from tgbot.lexicon.buttons import lexicon

from typing import Optional
from aiogram.filters.callback_data import CallbackData


class SelectWorkWayCallbackFactory(CallbackData, prefix="work_way"):
    action: str


class SelectNewWorkTypeCallbackFactory(CallbackData, prefix="new_work_type"):
    work_type: str

class StartNewWorkCallbackFactory(CallbackData, prefix="start_new_work"):
    action: str


def get_user_work_way_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon['new_work']['continue_last_work'],
        callback_data=SelectWorkWayCallbackFactory(action="continue_last_work"),
    )
    builder.button(
        text=lexicon['new_work']['start_new_work'],
        callback_data=SelectWorkWayCallbackFactory(action="start_new_work")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_new_work_types_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon['new_work']['ege'],
        callback_data=SelectNewWorkTypeCallbackFactory(work_type="ege"),
    )
    builder.button(
        text=lexicon['new_work']['topic'],
        callback_data=SelectNewWorkTypeCallbackFactory(work_type="topic")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_topics_kb(topics_list: list) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(
        text=lexicon['service']['back'],
    )
    for topic in topics_list:
        builder.button(
            text=topic.name,
        )
    builder.adjust(2)

    return builder.as_markup(resize_keyboard=True)

def get_start_work_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon['new_work']['start'],
        callback_data=StartNewWorkCallbackFactory(action="start"),
    )
    builder.button(
        text=lexicon['new_work']['cancel'],
        callback_data=StartNewWorkCallbackFactory(action="cancel")
    )
    builder.adjust(1)
    return builder.as_markup()
