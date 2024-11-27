import re

from aiogram import Router, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from db.crud import (get_user, create_user, get_hand_work, get_user_works)
from tgbot.handlers.menu import cmd_menu
from tgbot.keyboards.new_work import get_start_work_kb, get_user_work_way_kb
from tgbot.lexicon.messages import lexicon
from tgbot.states.register_user import InputUserName

router = Router()


@router.message(CommandStart(deep_link=True, magic=F.args.regexp(re.compile(r'(work)_\w+'))))
async def deep_linking(message: Message, command: CommandObject, state: FSMContext):
    identificator = command.args.split("_")[-1]
    work = get_hand_work(identificator=identificator)

    if work:
        works_list = get_user_works(message.from_user.id)
        if works_list and works_list[0].end_datetime is None:

            await message.answer(
                text=lexicon['new_work']['previous_work_not_ended'],
                reply_markup=get_user_work_way_kb(hand_work_id=identificator)
            )
        else:
            await message.answer(
                text=lexicon['new_work']['hand_work_caption'].format(work.name),
                reply_markup=get_start_work_kb(work_type="hand_work", hand_work_id=identificator)
            )

    else:
        await message.answer(
            text="Персональная тренировка с таким номером не найдена. Проверь правильность ссылки или обратись к преподавателю."
        )
        await cmd_menu(message, state)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)
    if user is None:
        await state.set_state(InputUserName.waiting_for_msg)
        await message.answer(
            text=lexicon['start']['hello'],
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await cmd_menu(message, state)


@router.message(InputUserName.waiting_for_msg)
async def register_user(message: Message, state: FSMContext):
    await state.clear()

    user_name = message.text.strip()
    if len(user_name) < 100:
        user_name = user_name.capitalize()
        user = create_user(user_name, message.from_user.id)
        await message.answer(
            text=lexicon['start']['reg_ok'].format(user.name)
        )
    else:
        await state.set_state(InputUserName.waiting_for_msg)
        await message.answer(
            text=lexicon['start']['bad_name']
        )
