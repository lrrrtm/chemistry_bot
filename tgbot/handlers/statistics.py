from os import getenv

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from db.crud import get_user_works
from tgbot.lexicon.messages import lexicon
from tgbot.lexicon.buttons import lexicon as btns_lexicon
from utils.user_statistics import get_user_statistics

router = Router()


@router.message(Command("stats"))
@router.message(F.text == btns_lexicon['main_menu']['stats'])
async def cmd_stats(message: Message, state: FSMContext):
    msg = await message.answer(
        text=lexicon['statistics']['search_for_data']
    )

    works_list = get_user_works(message.from_user.id)
    works_list = [el for el in works_list if el.end_datetime is not None][:10]

    await msg.delete()

    if works_list:
        text_to_send = f"<b>{btns_lexicon['main_menu']['stats']}</b>"
        stats_list = get_user_statistics(message.from_user.id)
        for index, stats_el in enumerate(stats_list):
            text_to_send += lexicon['statistics']['stats_block'].format(
                '',
                f"https://{getenv('DOMAIN')}",
                stats_el['general']['share_token'] or '',
                stats_el['general']['name'],
                '',
                stats_el['results']['final_mark'],
                stats_el['results']['max_mark'],
                stats_el['general']['time']['end'] - stats_el['general']['time']['start'],
            )

        # text_to_send += lexicon['statistics']['hint_to_open_stats']
        await message.answer(text_to_send)

    else:
        await message.answer(
            text=lexicon['statistics']['no_data']
        )
