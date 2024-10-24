from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from tgbot.lexicon.buttons import lexicon


def get_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text=lexicon['main_menu']['new_work'])
    )
    builder.row(
        KeyboardButton(text=lexicon['main_menu']['stats'])
    )

    return builder.as_markup(resize_keyboard=True)

def get_back_btn_kb(btn_text: str) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text=btn_text)
    )

    return builder.as_markup(resize_keyboard=True)