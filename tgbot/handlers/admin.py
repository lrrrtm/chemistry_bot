import hashlib
from datetime import datetime
from os import getenv

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove

from db.crud import get_all_users, get_all_topics, insert_topics_data
from redis_db.crud import set_temporary_key
from tgbot.handlers.check import cmd_check
from tgbot.handlers.trash import bot
from tgbot.keyboards.admin import get_admin_menu_main_kb, AdminMenuMainCallbackFactory, get_admin_system_status_kb, \
    AdminMenuBackCallbackFactory, AdminRebootServiceCallbackFactory, get_admin_db_kb, get_admin_cancel_upload_kb
from tgbot.lexicon.buttons import lexicon
from tgbot.states.updating_db import UpdateTopics
from utils.clearing import clear_folder
from utils.excel import export_topics_list, import_topics_list
from utils.services_checker import get_system_status

router = Router()


def get_admin_auth_key(telegram_id: int) -> str:
    input_string = f"{datetime.utcnow()}{telegram_id}"
    key = hashlib.sha256(input_string.encode()).hexdigest()

    set_temporary_key(
        key=str(telegram_id),
        value=key
    )

    return key


@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.chat.id in [int(getenv('FBACK_GROUP_ID')), int(getenv('ADMIN_ID'))]:
        await message.answer(
            text="<b>Панель управления</b>",
            reply_markup=get_admin_menu_main_kb(get_admin_auth_key(message.from_user.id), message.from_user.id)
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

    elif volume == "database":
        await callback.message.edit_text(
            text="<b>База данных</b>"
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_admin_db_kb(get_admin_auth_key(callback.from_user.id), callback.from_user.id)
        )

    elif volume == "update_topics_list":
        await callback.message.delete()

        topics_list = get_all_topics()
        export_topics_list(topics_list)

        await callback.message.answer_document(
            document=FSInputFile(f"{getenv('ROOT_FOLDER')}/data/temp/chembot_topics_list.xlsx"),
            caption=f"<b>Обновление базы тем/тегов</b>"
                    f"\n\nДля внесения изменений откройте эту таблицу, добавьте, измените или удалите нужные строки, после чего отправьте отредактированный файл обратно.",
            reply_markup=get_admin_cancel_upload_kb()
        )

        await state.set_state(UpdateTopics.waiting_for_msg)

    elif volume == "update_poll":
        await callback.message.delete()


@router.callback_query((AdminMenuBackCallbackFactory.filter()))
async def admin_menu_back_process(callback: types.CallbackQuery, callback_data: AdminMenuBackCallbackFactory,
                                  state: FSMContext):
    await callback.answer()
    current_volume = callback_data.current_volume

    await callback.message.delete()

    if current_volume == "system_status" or current_volume == "database":
        await cmd_admin(callback.message)


@router.callback_query((AdminRebootServiceCallbackFactory.filter()))
async def admin_menu_reboot_process(callback: types.CallbackQuery, callback_data: AdminRebootServiceCallbackFactory,
                                    state: FSMContext):
    filename = callback_data.filename

    await callback.answer(
        text=f"ℹ️ Запрос на перезагрузку {filename} отправлен!",
        show_alert=True
    )


@router.message(UpdateTopics.waiting_for_msg)
async def catch_topics_list_table(message: Message, state: FSMContext):
    if message.text == lexicon['admin']['cancel_uploading_table']:
        await state.clear()
        await message.answer(
            text="<b>Обновление данных отменено</b>",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        msg = await message.answer(
            text="Выполняется обработка файла...",
            reply_markup=ReplyKeyboardRemove()
        )
        file_id = message.document.file_id
        filepath = f"{getenv('ROOT_FOLDER')}/data/temp/recieved_topics_list.xlsx"
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, filepath)

        import_data = import_topics_list(filepath)

        await msg.delete()

        if import_data['is_ok']:
            filename = import_data['filename']
            insert_topics_data(import_data['data'])
            await message.answer_document(
                document=FSInputFile(f"{getenv('ROOT_FOLDER')}/data/temp/{filename}"),
                caption="<b>Обновление базы тем/тегов</b>"
                     "\n\nДанные успешно обновлены. В файле приведена информация о результатах импорта."
            )
        else:
            await message.answer(
                text="<b>Ошибка при импорте файла</b>"
                     f"\n\nПри обработке отправленного вами файла произошла следующая ошибка: {import_data['comment']}"
            )

    clear_folder(f"{getenv('ROOT_FOLDER')}/data/temp")
