from typing import List

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from db.crud import (get_user, get_user_works, get_topic_by_id, get_work_questions, get_all_topics)
from db.models import Pool
from tgbot.keyboards.new_work import get_user_work_way_kb, SelectWorkWayCallbackFactory, get_new_work_types_kb, \
    SelectNewWorkTypeCallbackFactory, get_topics_kb, get_start_work_kb
from tgbot.lexicon.messages import lexicon
from tgbot.lexicon.buttons import lexicon as btns_lexicon

router = Router()


@router.message(Command("new_work"))
@router.message(F.text == btns_lexicon['main_menu']['new_work'])
async def cmd_new_work(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user is None:
        await message.answer(
            text="Для того, чтобы использовать эту команду, необходимо зарегистрироваться. Напиши или нажми /start"
        )
    else:
        works_list = get_user_works(message.from_user.id)
        if works_list and works_list[0].end_datetime is None:

            await message.answer(
                text="У тебя есть незаконченное задание, можем закончить его или создать новое. Как поступим?",
                reply_markup=get_user_work_way_kb()
            )
        else:
            await message.answer(
                text=f"<b>{btns_lexicon['main_menu']['new_work']}</>"
                     f"\n\nВыбери, что ты хочешь начать решать",
                reply_markup=get_new_work_types_kb()
            )


@router.callback_query(SelectWorkWayCallbackFactory.filter())
async def process_user_work_way(callback: types.CallbackQuery, callback_data: SelectWorkWayCallbackFactory,
                                state: FSMContext):
    await callback.answer()
    action = callback_data.action

    if action == 'start_new_work':
        await callback.message.edit_text(
            text=f"<b>{btns_lexicon['main_menu']['new_work']}</>"
                 f"\n\nВыбери, что ты хочешь начать решать"
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_new_work_types_kb()
        )
    elif action == 'continue_last_work':
        pass


@router.callback_query(SelectNewWorkTypeCallbackFactory.filter())
async def process_user_work_way(callback: types.CallbackQuery, callback_data: SelectNewWorkTypeCallbackFactory,
                                state: FSMContext):
    await callback.answer()
    action = callback_data.work_type

    if action == "ege":
        await callback.message.edit_text(
            text=f"<b>{btns_lexicon['main_menu']['new_work']}</b>"
                 f"\n\nМы составим для тебя вариант из 34 заданий. "
                 f"После каждого задания будет необходимо отправить ответ в таком виде, который требует конкретное задание. Твои решения задания из второй части КИМа тебе нужно будет оценить самостоятельно."
                 f"\n\nКак только ты будешь готов(-а), нажми на кнопку под этим сообщением."
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_start_work_kb()
        )

    elif action == "topic":
        await callback.message.delete()

        topics_list = get_all_topics()
        # todo: установка state на прослушку выбора темы на клавиатуре, после чего get_start_work_kb()
        await callback.message.answer(
            text=f"<b>{btns_lexicon['main_menu']['new_work']}</b>"
                 "\n\nВыбери из списка тему, на которую ты хочешь решать задания",
            reply_markup=get_topics_kb(topics_list)
        )
