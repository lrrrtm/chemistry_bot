from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.formatting import (
    Bold, as_list, as_marked_section, as_key_value, HashTag
)

from db.crud import (get_user, get_user_works, get_topic, get_work_questions)
from tgbot.keyboards.menu import get_menu_kb
from tgbot.lexicon.messages import lexicon
from tgbot.lexicon.buttons import lexicon as btns_lexicon
from utils.user_statistics import get_user_statistics

router = Router()


@router.message(Command("stats"))
@router.message(F.text == btns_lexicon['main_menu']['stats'])
async def cmd_stats(message: Message, state: FSMContext):
    msg = await message.answer(
        text="Собираем твою статистику..."
    )

    works_list = get_user_works(message.from_user.id)
    works_list = works_list[::-1]

    await msg.delete()

    if works_list:
        text_to_send = f"<b>{btns_lexicon['main_menu']['stats']}</b>\n\n"
        stats_list = get_user_statistics(message.from_user.id)
        for index, stats_el in enumerate(stats_list):
            text_to_send += (f"{index + 1}. <b>{stats_el['general']['name']} <a href='https://crodconnect.ru/stats?uuid={None}&tid={message.from_user.id}&work={stats_el['general']['work_id']}'>#{stats_el['general']['work_id']}</a></b>"
                             f"\n    📑 {stats_el['results']['final_mark']}/{stats_el['results']['max_mark']}"
                             f"\n    ⌛ {stats_el['general']['time']['end'] - stats_el['general']['time']['start']}")

        text_to_send += "\n\n<b>Нажми на номер задания, который обозначен символом <code>#</code>, чтобы посмотреть подробную статистику по решённому варианту</b>"
        await message.answer(text_to_send)

    else:
        await message.answer(
            text=f"У тебя ещё ни одного завершённого задания, чтобы мы могли собрать статистику. \n\nНачни решать, нажав на кнопку <b>«{btns_lexicon['main_menu']['new_work']}»</b>"
        )
