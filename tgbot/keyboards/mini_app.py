from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.mini_app_links import get_tma_share_link, get_tma_start_url, is_public_web_app_url


def get_open_mini_app_kb(button_text: str, startapp: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    web_app_url = get_tma_start_url(startapp)
    share_link = get_tma_share_link(startapp)

    if web_app_url and is_public_web_app_url(web_app_url):
        builder.button(
            text=button_text,
            web_app=WebAppInfo(url=web_app_url),
        )
    elif share_link:
        builder.button(
            text=button_text,
            url=share_link,
        )
    else:
        raise RuntimeError("Mini App URL is not configured. Set DOMAIN or BOT_NAME.")

    builder.adjust(1)
    return builder.as_markup()
