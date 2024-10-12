from os import getenv

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from db.crud import get_all_users
from tgbot.handlers.check import cmd_check
from tgbot.keyboards.admin import get_admin_menu_main_kb, AdminMenuMainCallbackFactory

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.chat.id == int(getenv('FBACK_GROUP_ID')):
        await message.answer(
            text="<b>Панель управления</b>",
            reply_markup=get_admin_menu_main_kb()
        )


@router.callback_query(AdminMenuMainCallbackFactory.filter())
async def admin_menu_main_process(callback: types.CallbackQuery, callback_data: AdminMenuMainCallbackFactory,
                                  state: FSMContext):
    await callback.answer()
    volume = callback_data.volume

    if volume == "create_topic_work":
        pass

    elif volume == "system_status":
        await cmd_check(callback.message)
