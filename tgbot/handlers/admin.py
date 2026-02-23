import os.path
import subprocess
from datetime import datetime
from os import getenv

from aiogram import Router, types, exceptions
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove

from db.crud import get_all_topics, insert_topics_data, insert_pool_data, get_all_users
from tgbot.handlers.trash import bot
from tgbot.keyboards.admin import get_admin_menu_main_kb, AdminMenuMainCallbackFactory, get_admin_system_status_kb, \
    AdminMenuBackCallbackFactory, AdminRebootServiceCallbackFactory, get_admin_db_kb, get_admin_cancel_upload_kb, \
    get_admin_pool_menu_kb, get_admin_sender_kb
from tgbot.lexicon.buttons import lexicon
from tgbot.lexicon.messages import lexicon as msg_lexicon
from tgbot.states.updating_db import UpdateTopics, InsertPool
from tgbot.states.writing_sender_text import InputMessage
from utils.clearing import clear_folder, clear_trash_by_db
from utils.excel import export_topics_list, import_topics_list, import_pool
from utils.move_file import move_image
from utils.services_checker import get_system_status

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.chat.id in [int(getenv('ADMIN_ID')), int(getenv('DEVELOPER_ID'))]:
        await message.answer(
            text="<b>🎛️ Панель управления</b>"
                 "\n\nВыберите необходимый раздел",
            reply_markup=get_admin_menu_main_kb()
        )


@router.message(Command("cleardb"))
async def cmd_cleardb(message: types.Message):
    if message.chat.id in [int(getenv('ADMIN_ID')), int(getenv('DEVELOPER_ID'))]:
        for dir in [f"{os.getenv('ROOT_FOLDER')}/data/images/questions",
                    f"{os.getenv('ROOT_FOLDER')}/data/images/answers"]:
            count = clear_trash_by_db(dir)
            await message.answer(
                text=f"{dir.split('/')[-1]}: {count}"
            )


@router.callback_query(AdminMenuMainCallbackFactory.filter())
async def admin_menu_main_process(callback: types.CallbackQuery, callback_data: AdminMenuMainCallbackFactory,
                                  state: FSMContext):
    await callback.answer()
    volume = callback_data.volume

    if volume == "system_status":
        data = get_system_status()

        await callback.message.edit_text(
            text=f"<b>{lexicon['admin']['system_status']}</b>"
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_admin_system_status_kb(data)
        )

    elif volume == "database":
        await callback.message.edit_text(
            text=f"<b>{lexicon['admin']['database']}</b>"
        )
        await callback.message.edit_reply_markup(
            reply_markup=get_admin_db_kb()
        )

    elif volume == "update_topics_list":
        await callback.message.delete()

        topics_list = get_all_topics(active=True)
        export_topics_list(topics_list)

        await callback.message.answer_document(
            document=FSInputFile(f"{getenv('ROOT_FOLDER')}/data/temp/chembot_topics_list.xlsx"),
            caption=f"<b>{lexicon['admin']['update_topics_list']}</b>"
                    f"\n\n1. Откройте файл, отправленный в этом сообщении"
                    f"\n2. Перейдите на лист MAIN"
                    f"\n3. Удалите ненужные и/или добавьте новые строки с названиями тем и тегами"
                    f"\n4. Сохраните файл и отправьте его обратным сообщением."
                    f"\n\nP.S. В одной строке должен содержаться только 1 тег",
            reply_markup=get_admin_cancel_upload_kb()
        )

        await state.set_state(UpdateTopics.waiting_for_msg)

    elif volume == "pool_menu":
        await callback.message.edit_text(
            text=f"<b>{lexicon['admin']['update_pool']}</b>"
        )

        await callback.message.edit_reply_markup(
            reply_markup=get_admin_pool_menu_kb()
        )

    elif volume == "insert_pool":
        await callback.message.answer_document(
            document=FSInputFile(f"{getenv('ROOT_FOLDER')}/data/excel_templates/chembot_pool_list.xlsx"),
            caption=f"<b>{lexicon['admin']['insert_pool']}</b>"
                    f"\n\nДля добавления новых вопросов откройте эту таблицу, внесите все данные, после чего отправьте отредактированный файл обратно.",
            reply_markup=get_admin_cancel_upload_kb()
        )

        await state.set_state(InsertPool.waiting_for_msg)

    elif volume == "sender":
        await callback.message.delete()

        await callback.message.answer(
            text=f"<b>{lexicon['admin']['sender']}</b>"
                 f"\n\nНапишите и отправьте текст рассылки для всех пользователей",
            reply_markup=get_admin_cancel_upload_kb()
        )

        await state.set_state(InputMessage.waiting_for_msg)

    elif volume == "accept_sender":
        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        msg = await bot.send_message(
            chat_id=callback.from_user.id,
            text=f"<b>{lexicon['admin']['sender']}</b>"
                 f"\n\nИдёт рассылка пользователям: 0%"
        )

        data = await state.get_data()
        html_text = data.get('html_text')

        users_list = get_all_users()

        sended_counter = 0

        for user in users_list:
            try:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=html_text,
                )
            except exceptions.TelegramBadRequest:
                pass

            sended_counter += 1
            cur_percent = int(sended_counter / len(users_list) * 100)

            if cur_percent % 10 == 0 and cur_percent != 100:
                await msg.edit_text(
                    text=f"<b>{lexicon['admin']['sender']}</b>"
                         f"\n\nИдёт рассылка пользователям: {cur_percent}%"
                )

            elif cur_percent == 100:
                await msg.edit_text(
                    text=f"<b>{lexicon['admin']['sender']}</b>"
                         f"\n\nРассылка успешно завершена!"
                )


    elif volume == "decline_sender":
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
        await callback.message.answer(
            text=f"{msg_lexicon['service']['action_cancelled']}",
            reply_markup=ReplyKeyboardRemove()
        )


@router.message(InputMessage.waiting_for_msg)
async def admin_menu_sender_process(message: Message, state: FSMContext):
    await state.clear()

    if message.text == lexicon['admin']['cancel_uploading_table']:
        await message.answer(
            text=f"{msg_lexicon['service']['action_cancelled']}",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await state.update_data(html_text=message.html_text)

        await message.answer(
            text=f"<b>{lexicon['admin']['sender']}</b>"
                 f"\n\nСообщение будет выглядеть так",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
            text=message.html_text,
        )
        await message.answer(
            text=f"<b>{lexicon['admin']['sender']}</b>"
                 f"\n\nПодтвердите корректность текста рассылки перед отправкой",
            reply_markup=get_admin_sender_kb()
        )


@router.callback_query((AdminMenuBackCallbackFactory.filter()))
async def admin_menu_back_process(callback: types.CallbackQuery, callback_data: AdminMenuBackCallbackFactory,
                                  state: FSMContext):
    await callback.answer()
    current_volume = callback_data.current_volume

    await callback.message.delete()

    if current_volume in ["system_status", "database"]:
        await cmd_admin(callback.message)

    elif current_volume == "pool_menu":
        await callback.message.answer(
            text=f"<b>{lexicon['admin']['database']}</b>",
            reply_markup=get_admin_db_kb()
        )


@router.callback_query((AdminRebootServiceCallbackFactory.filter()))
async def admin_menu_reboot_process(callback: types.CallbackQuery, callback_data: AdminRebootServiceCallbackFactory,
                                    state: FSMContext):
    filename = callback_data.filename

    await callback.answer(
        text=f"ℹ️ Запрос на перезапуск службы {filename} отправлен!",
        show_alert=True
    )

    try:
        subprocess.run(["docker", "restart", filename], check=True)

    except subprocess.CalledProcessError as e:
        await callback.message.answer(
            text=f"🚨 Ошибка при перезапуске службы <b>{filename}</b>"
                 f"\n\n{e}"
        )


@router.message(UpdateTopics.waiting_for_msg)
async def catch_topics_list_table(message: Message, state: FSMContext):
    if message.text == lexicon['admin']['cancel_uploading_table']:
        await state.clear()
        await message.answer(
            text=f"{msg_lexicon['service']['action_cancelled']}",
            reply_markup=ReplyKeyboardRemove()
        )

    else:
        msg = await message.answer(
            text=f"{msg_lexicon['service']['processing_file']}",
            reply_markup=ReplyKeyboardRemove()
        )
        file_id = message.document.file_id
        filepath = f"{getenv('ROOT_FOLDER')}/data/temp/topics_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, filepath)

        # todo: реализовать обратную связь по загруженным данным
        import_data = import_topics_list(filepath)

        await msg.delete()

        if import_data['is_ok']:
            filename = import_data['filename']
            insert_topics_data(import_data['data'])
            await message.answer_document(
                document=FSInputFile(f"{getenv('ROOT_FOLDER')}/data/temp/{filename}"),
                caption=f"<b>{lexicon['admin']['update_topics_list']}</b>"
                        "\n\nДанные успешно обновлены. В файле приведена информация о результатах импорта."
            )
        else:
            await message.answer(
                text=msg_lexicon['service']['processing_file_error'].format(import_data['comment'])
            )

    clear_folder(f"{getenv('ROOT_FOLDER')}/data/temp")


@router.message(InsertPool.waiting_for_msg)
async def catch_pool_list_table(message: Message, state: FSMContext):
    if message.text == lexicon['admin']['cancel_uploading_table']:
        await state.clear()
        await message.answer(
            text=msg_lexicon['service']['action_cancelled'],
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        msg = await message.answer(
            text=msg_lexicon['service']['processing_file'],
            reply_markup=ReplyKeyboardRemove()
        )
        file_id = message.document.file_id
        filepath = f"{getenv('ROOT_FOLDER')}/data/temp/pool_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, filepath)

        import_data = import_pool(filepath)
        await msg.delete()

        if import_data['is_ok']:
            if len(import_data['errors']) == 0:
                pool = insert_pool_data(import_data['data'])

                for el in pool:
                    if bool(el.question_image):
                        if os.path.exists(f"{getenv('ROOT_FOLDER')}/data/temp/q_{el.import_id}.png"):
                            move_image(
                                source_path=f"{getenv('ROOT_FOLDER')}/data/temp/q_{el.import_id}.png",
                                destination_path=f"{getenv('ROOT_FOLDER')}/data/images/questions/{el.id}.png"
                            )
                        else:
                            pass

                    if bool(el.answer_image):
                        if os.path.exists(f"{getenv('ROOT_FOLDER')}/data/temp/a_{el.import_id}.png"):
                            move_image(
                                source_path=f"{getenv('ROOT_FOLDER')}/data/temp/a_{el.import_id}.png",
                                destination_path=f"{getenv('ROOT_FOLDER')}/data/images/answers/{el.id}.png"
                            )
                        else:
                            pass

                await message.answer(
                    text=f"<b>{lexicon['admin']['insert_pool']}</b>"
                         f"\n\nВопросы успешно импортированы ({len(import_data['data'])}/{len(import_data['data'])})"
                )
            else:
                ids = " ".join(str(a) for a in import_data['errors'])
                await message.answer(
                    text=f"<b>{lexicon['admin']['insert_pool']}</b>"
                         f"\n\nВопросы не были добавлены из-за наличия ошибок в заполнении полей в следующих строках: \n\n{ids}"
                         f"\n\nПосле устранение ошибок вызовите /admin заново и повторите загрузку вопросов"
                )

        else:
            await message.answer(
                text=msg_lexicon['service']['processing_file_error'].format(import_data['comment'])
            )

    clear_folder(f"{getenv('ROOT_FOLDER')}/data/temp")
