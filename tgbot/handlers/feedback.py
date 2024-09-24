import html
from os import getenv

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from db.crud import get_user
from tgbot.handlers.start import cmd_start
from tgbot.handlers.trash import bot
from tgbot.keyboards.feedback import get_answer_to_user_kb, AnswerToUserCallbackFactory, get_cancel_answer_kb
from tgbot.keyboards.menu import get_back_btn_kb
from tgbot.lexicon.messages import lexicon
from tgbot.lexicon.buttons import lexicon as btns_lexicon
from tgbot.states.answering_to_user import InputAdminMessage
from tgbot.states.feedback_waiting import InputUserMessage

router = Router()

data_to_send = {}


@router.message(Command("feedback"))
async def cmd_feedback(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user is not None:
        await message.answer(
            text=lexicon['feedback']['ask_to'],
            reply_markup=get_back_btn_kb(btns_lexicon['service']['main_menu'])
        )
        await state.set_state(InputUserMessage.waiting_for_msg)
    else:
        await message.answer(
            text=lexicon['service']['need_reg'],
        )


@router.message(InputUserMessage.waiting_for_msg)
async def fback_process(message: Message, state: FSMContext):
    await state.clear()
    if message.text == btns_lexicon['service']['main_menu']:
        await message.answer(
            text=lexicon['feedback']['user_cancelled_fback']
        )
    else:
        user_text = html.escape(message.text)
        user = f"@{message.from_user.username} ({message.from_user.first_name})" or message.from_user.first_name

        await bot.send_message(
            chat_id=getenv('FBACK_GROUP_ID'),
            text=lexicon['feedback']['new_ask'].format(user, user_text),
            reply_markup=get_answer_to_user_kb(message.from_user.id)
        )
        await message.answer(
            text=lexicon['feedback']['ask_sended'].format(user_text)
        )
    await cmd_start(message, state)


@router.callback_query(AnswerToUserCallbackFactory.filter())
async def answer_to_user_step_1(callback: types.CallbackQuery, callback_data: AnswerToUserCallbackFactory,
                                state: FSMContext):
    await callback.answer()
    await state.set_state(InputAdminMessage.waiting_for_msg)
    data_to_send['tid'] = callback_data.tid
    data_to_send['message_id'] = callback.message.message_id
    await callback.message.answer(
        text=lexicon['feedback']['write_text_to_send'],
        reply_markup=get_cancel_answer_kb()
    )


@router.message(InputAdminMessage.waiting_for_msg)
async def answer_to_user_step_2(message: types.Message, state: FSMContext):
    await state.clear()
    if message.text == btns_lexicon['feedback']['cancel_answer']:
        await message.answer(
            text=lexicon['feedback']['answer_to_user_cancelled'],
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        admin_text = html.escape(message.text.strip())
        await bot.send_message(
            chat_id=data_to_send['tid'],
            text=lexicon['feedback']['answer_recieved'].format(admin_text),
        )
        await message.answer(
            text=lexicon['feedback']['answer_sended_to_user'].format(admin_text),
            reply_markup=ReplyKeyboardRemove()
        )
        try:
            await bot.edit_message_reply_markup(
                chat_id=message.from_user.id,
                message_id=data_to_send['message_id'],
                reply_markup=None
            )
        except Exception as e:
            pass
