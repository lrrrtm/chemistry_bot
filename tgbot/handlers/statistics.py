from datetime import datetime
from os import getenv

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.formatting import (
    Bold, as_list, as_marked_section, as_key_value, HashTag
)

from db.crud import (get_user, get_user_works, get_topic_by_id, get_work_questions)
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

    await msg.delete()

    if works_list:
        text_to_send = f"<b>{btns_lexicon['main_menu']['stats']}</b>"
        stats_list = get_user_statistics(message.from_user.id)
        for index, stats_el in enumerate(stats_list):
            text_to_send += lexicon['statistics']['stats_block'].format(
                # index + 1,
                '',
                stats_el['general']['name'],
                get_user(message.from_user.id).id,
                message.from_user.id,
                stats_el['general']['work_id'],
                stats_el['general']['work_id'],
                stats_el['results']['final_mark'],
                stats_el['results']['max_mark'],
                stats_el['general']['time']['end'] - stats_el['general']['time']['start'],
                getenv('STATS_HOST')
            )

        text_to_send += lexicon['statistics']['hint_to_open_stats']
        await message.answer(text_to_send)

    else:
        await message.answer(
            text=lexicon['statistics']['no_data']
        )
