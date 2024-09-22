from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from tgbot.lexicon.buttons import lexicon

from typing import Optional
from aiogram.filters.callback_data import CallbackData


class AnswerToUserCallbackFactory(CallbackData, prefix="answerto"):
    tid: int


def get_answer_to_user_kb(user_tid: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon['feedback']['answer_to_user'],
        callback_data=AnswerToUserCallbackFactory(tid=user_tid)
    )
    return builder.as_markup()


def get_cancel_answer_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(
        text=lexicon['feedback']['cancel_answer']
    )
    return builder.as_markup(resize_keyboard=True)
