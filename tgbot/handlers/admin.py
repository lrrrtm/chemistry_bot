import hashlib
from datetime import datetime
from os import getenv

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from db.crud import get_all_users
from redis_db.crud import set_temporary_key
from tgbot.handlers.check import cmd_check
from tgbot.keyboards.admin import get_admin_menu_main_kb, AdminMenuMainCallbackFactory, get_admin_system_status_kb, \
    AdminMenuBackCallbackFactory, AdminRebootServiceCallbackFactory
from utils.services_checker import get_system_status

router = Router()


def get_admin_auth_key(message: types.Message) -> str:
    input_string = f"{datetime.utcnow()}{message.from_user.id}"
    key = hashlib.sha256(input_string.encode()).hexdigest()

    set_temporary_key(
        key=str(message.from_user.id),
        value=key
    )

    return key


@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.chat.id in [int(getenv('FBACK_GROUP_ID')), int(getenv('ADMIN_ID'))]:
        await message.answer(
            text="<b>Панель управления</b>",
            reply_markup=get_admin_menu_main_kb(get_admin_auth_key(message), message.from_user.id)
        )


@router.callback_query(AdminMenuMainCallbackFactory.filter())
async def admin_menu_main_process(callback: types.CallbackQuery, callback_data: AdminMenuMainCallbackFactory,
                                  state: FSMContext):
    await callback.answer()
    volume = callback_data.volume

    if volume == "system_status":
        data = get_system_status()

        await callback.message.edit_text(
            text="<b>Состояние системы</b>"
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_admin_system_status_kb(data)
        )


@router.callback_query((AdminMenuBackCallbackFactory.filter()))
async def admin_menu_back_process(callback: types.CallbackQuery, callback_data: AdminMenuBackCallbackFactory,
                                  state: FSMContext):
    await callback.answer()
    current_volume = callback_data.current_volume

    await callback.message.delete()

    if current_volume == "system_status":
        await cmd_admin(callback.message)


@router.callback_query((AdminRebootServiceCallbackFactory.filter()))
async def admin_menu_reboot_process(callback: types.CallbackQuery, callback_data: AdminRebootServiceCallbackFactory,
                                    state: FSMContext):
    filename = callback_data.filename

    await callback.answer(
        text=f"ℹ️ Запрос на перезагрузку {filename} отправлен!",
        show_alert=True
    )
