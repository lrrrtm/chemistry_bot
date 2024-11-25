import hashlib
import os
import platform
import re
import sys
from datetime import datetime
from typing import List

import telebot
from flet_core import FilePickerUploadFile

from redis_db.crud import get_value, set_temporary_key
from utils.image_converter import image_to_base64
from utils.move_file import move_image
from utils.tags_helper import get_random_questions, get_random_questions_for_hard_tags_filter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from os import getenv
from urllib.parse import urlparse, parse_qs
import flet as ft
from utils.user_statistics import get_user_statistics
from db.crud import get_work_by_url_data, get_work_questions_joined_pool, get_all_users, get_all_questions, \
    insert_new_hand_work, get_ege_converting, update_ege_converting, get_all_pool, \
    get_question_from_pool, deactivate_question, update_question, \
    switch_image_flag, get_topics_table, insert_question_into_pool, remove_user
from db.models import WorkQuestion, Pool
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(token=getenv('BOT_API_KEY'), parse_mode='html')

if platform.system() == "Windows":
    set_temporary_key(
        'develop',
        'develop',
        3600
    )


def get_info_column(caption: str, icon_filename: str, progress_bar_visible: bool = False) -> ft.Column:
    error_column = ft.Column(
        controls=[
            ft.Image(
                src=f"/images/{icon_filename}",
                error_content=ft.Icon(ft.icons.ERROR, size=50),
                width=150
            ),
            ft.Text(caption, size=16,
                    text_align=ft.TextAlign.CENTER),
            ft.ProgressBar(
                visible=progress_bar_visible,
                width=100
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        width=300
    )

    return error_column


def get_general_info_card(stats: dict, detailed: bool = False):
    card_conrols_list = [
        ft.Container(
            content=ft.ListTile(
                leading=ft.Icon(ft.icons.SCHOOL),
                title=ft.Text(stats['general']['name']),
                subtitle=ft.Text("название работы"),
            ),
            padding=ft.padding.only(left=-15, bottom=-25)
        ),
        ft.Container(
            content=ft.ListTile(
                leading=ft.Icon(ft.icons.ACCESS_TIME),
                title=ft.Text(f"{stats['general']['time']['end'] - stats['general']['time']['start']}"),
                subtitle=ft.Text("затраченное время"),
            ),
            padding=ft.padding.only(left=-15, bottom=-25)
        ),
        ft.Container(
            content=ft.ListTile(
                leading=ft.Icon(ft.icons.INSERT_CHART),
                title=ft.Text(f"{stats['results']['final_mark']} из {stats['results']['max_mark']}"),
                subtitle=ft.Text("результат"),
            ),
            padding=ft.padding.only(left=-15, bottom=-10)
        ),
        ft.Divider(thickness=1),
        ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("полностью"),
                        ft.Text(f"{len(stats['questions']['fully'])}", size=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text("частично"),
                        ft.Text(f"{len(stats['questions']['semi'])}", size=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text("не решено"),
                        ft.Text(f"{len(stats['questions']['zero'])}", size=16),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    ]

    if detailed:
        card_conrols_list.insert(
            0,
            ft.Container(
                content=ft.ListTile(
                    leading=ft.Icon(ft.icons.ACCOUNT_CIRCLE),
                    title=ft.Text(stats['general']['user'].name),
                    subtitle=ft.Text("ученик"),
                ),
                padding=ft.padding.only(left=-15, bottom=-25)
            ),
        )
        card_conrols_list.insert(
            1,
            ft.Container(
                content=ft.ListTile(
                    leading=ft.Icon(ft.icons.CALENDAR_TODAY),
                    title=ft.Text(stats['general']['time']['end'].strftime('%d.%m.%Y в %H:%M')),
                    subtitle=ft.Text("дата выполнения"),
                ),
                padding=ft.padding.only(left=-15, bottom=-25)
            ),
        )

    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Общий обзор", size=20),
                ],

            ),
            padding=15
        )
    )

    card.content.content.controls += card_conrols_list

    return card


def get_questions_info_card(questions_list: List[WorkQuestion], detailed: bool = False) -> ft.Card:
    card_controls = [ft.Container(ft.Text("Подробности", size=20), padding=ft.padding.only(left=10, top=10))]

    for index, question in enumerate(questions_list):

        if question.full_mark == question.user_mark:
            card_color = ft.colors.GREEN
        elif 0 < question.user_mark < question.full_mark:
            card_color = ft.colors.AMBER
        else:
            card_color = ft.colors.RED

        card_controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(ft.Row(
                                [ft.Icon(ft.icons.CIRCLE, color=card_color), ft.Text(f"№ {index + 1} (id{question.question_id})", size=18)]),
                                padding=ft.padding.only(left=10, top=10)),
                            ft.Image(
                                src_base64=image_to_base64(
                                    image_type="question",
                                    question_id=question.question_id
                                ) if bool(question.question_image) else None,
                                error_content=ft.Text("Не удалось загрузить изображение с заданием", size=14),
                                # border_radius=10,
                                visible=bool(question.question_image)
                            ),
                            ft.ListTile(
                                title=ft.Text(f"{question.text}"),
                                subtitle=ft.Column(
                                    [
                                        ft.Divider(thickness=1),
                                        ft.Text(
                                            f"Баллы: {question.user_mark} из {question.full_mark}\nВерный ответ: {question.answer}\n{'Твой ответ' if not detailed else 'Ответ ученика'}: {question.user_answer}")
                                    ]
                                ),
                            )
                        ]
                    )
                ),
                surface_tint_color=card_color,
            )
        )

    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=card_controls

            ),
            padding=5
        )
    )

    return card


def main(page: ft.Page):
    page.title = "ХимБот"
    page.padding = 0
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    page.theme_mode = ft.ThemeMode.DARK

    loading_bar = ft.ProgressBar(visible=False)
    page.overlay.append(loading_bar)

    # file_picker = ft.FilePicker(on_result=upload_files)
    # page.overlay.append(file_picker)

    upload_question_image_col = ft.Column()
    upload_answer_image_col = ft.Column()

    def switch_loading(value: bool):
        loading_bar.visible = value

        page.update()

    def change_new_work_questions_count(e: ft.ControlEvent):
        config = page.session.get("new_topic_work_config")

        if config is not None and e.control.value and e.control.value.isdigit():
            config['questions_count'] = int(e.control.value)
        else:
            config = {'questions_count': int(e.control.value), 'questions': {}, 'name': None}

        page.session.set(
            "new_topic_work_config",
            config,
        )

    def change_new_work_name(e: ft.ControlEvent):
        config = page.session.get("new_topic_work_config")

        if config is not None:
            config['name'] = e.control.value
        else:
            config = {'name': e.control.value, 'questions': {}}

        page.session.set(
            "new_topic_work_config",
            config,
        )

        print(config)

    def upload_files(e):
        if file_picker.result is not None and file_picker.result.files is not None:
            file = file_picker.result.files[-1]
            upload_list = [
                FilePickerUploadFile(
                    file.name,
                    upload_url=page.get_upload_url(file.name, 600),
                )
            ]
            file_picker.upload(upload_list)

    def upload_files_2(e):
        if new_file_picker.result is not None and new_file_picker.result.files is not None:
            file = new_file_picker.result.files[-1]
            upload_list = [
                FilePickerUploadFile(
                    file.name,
                    upload_url=page.get_upload_url(file.name, 600),
                )
            ]
            new_file_picker.upload(upload_list)

    def update_images_in_db(filepath: str):
        upload_image_config = page.session.get('upload_image_config')

        if os.path.exists(filepath):
            switch_image_flag(1, upload_image_config['type'], upload_image_config['id'])

    def process_update_image(e: ft.FilePickerUploadEvent):
        if bool(int(e.progress)):
            upload_image_config = page.session.get('upload_image_config')

            if upload_image_config['type'] == "question":
                filepath = f"{getenv('ROOT_FOLDER')}/data/questions_images/{upload_image_config['id']}.png"

            elif upload_image_config['type'] == "answer":
                filepath = f"{getenv('ROOT_FOLDER')}/data/answers_images/{upload_image_config['id']}.png"

            move_image(
                source_path=f"{getenv('ROOT_FOLDER')}/data/uploads/{e.file_name}",
                destination_path=filepath,
            )

            update_images_in_db(filepath)

            page.route = f"/admin/pool?update_question_id={upload_image_config['id']}"
            navigate()

    def process_upload_image(e: ft.FilePickerUploadEvent):
        if bool(int(e.progress)):
            upload_image_config = page.session.get('upload_new_image_config')
            upload_id = upload_image_config['upload_id']

            gen_data = page.session.get('gen_upload_data')

            filepath = f"{getenv('ROOT_FOLDER')}/data/temp/{upload_id}.png"
            move_image(
                source_path=f"{getenv('ROOT_FOLDER')}/data/uploads/{e.file_name}",
                destination_path=filepath,
            )

            gen_upload_data = page.session.get('gen_upload_data')
            if 'question_img_id' in gen_upload_data.keys() and gen_upload_data['question_img_id'] == upload_id:
                upload_question_image_col.controls = [
                    ft.Image(
                        src_base64=image_to_base64('temp', upload_id)
                    )
                ]
                gen_data['q_img'] = {'uploaded': True, 'id': upload_id}

            elif 'answer_img_id' in gen_upload_data.keys() and gen_upload_data['answer_img_id'] == upload_id:
                upload_answer_image_col.controls = [
                    ft.Image(
                        src_base64=image_to_base64('temp', upload_id)
                    )
                ]
                gen_data['a_img'] = {'uploaded': True, 'id': upload_id}

            page.session.set('gen_upload_data', gen_data)
            page.update()

    def remove_image_from_question(e: ft.ControlEvent):
        image_data = e.control.data

        if image_data['type'] == "question":
            old_filepath = f"{getenv('ROOT_FOLDER')}/data/questions_images/{image_data['id']}.png"
            new_filepath = f"{getenv('ROOT_FOLDER')}/data/questions_images/removed_{datetime.now().timestamp()}_{image_data['id']}.png"

        elif image_data['type'] == "answer":
            old_filepath = f"{getenv('ROOT_FOLDER')}/data/answers_images/{image_data['id']}.png"
            new_filepath = f"{getenv('ROOT_FOLDER')}/data/answers_images/removed_{datetime.now().timestamp()}_{image_data['id']}.png"

        if os.path.exists(old_filepath):
            os.rename(
                old_filepath,
                new_filepath
            )

            switch_image_flag(0, image_data['type'], image_data['id'])

            info_dialog.title.value = "Удаление изображения"
            info_dialog.content.value = "Изображение успешно удалено!"
            info_dialog.open = True

            page.update()

    file_picker = ft.FilePicker(on_result=upload_files, on_upload=process_update_image)
    new_file_picker = ft.FilePicker(on_result=upload_files_2, on_upload=process_upload_image)
    page.overlay.append(file_picker)
    page.overlay.append(new_file_picker)

    def change_count_of_questions(e: ft.ControlEvent):
        data = e.control.data
        tag = data['tag']

        config = page.session.get("new_topic_work_config")
        questions = config['questions']

        if e.control.value:
            if e.control.value.isnumeric() and e.control.value != "0":
                questions[tag] = int(e.control.value)
            elif e.control.value == "0":
                questions.pop(tag)
        else:
            try:
                questions.pop(tag)
            except Exception:
                pass

        config['questions'] = questions
        page.session.set(
            "new_topic_work_config",
            config,
        )

        print(config)

    def generate_new_topic_work_with_hard_tags_filter():
        data = page.session.get("new_topic_work_config")
        name = data['name']
        questions_count = data['questions_count']
        tags_list = list(data['questions'].values())

        all_questions_list = get_all_questions()

        if len(tags_list) > 1:
            questions_ids_pool = get_random_questions_for_hard_tags_filter(pool=all_questions_list, tags_list=tags_list,
                                                                           questions_count=questions_count)
            if questions_ids_pool['is_ok']:
                work = insert_new_hand_work(
                    name=name if name else f"Тренировка {datetime.now().strftime('%Y%m%d%H%M')}",
                    identificator=hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:6],
                    questions_ids_list=questions_ids_pool['detail']
                )

                bot.send_message(
                    chat_id=getenv('ADMIN_ID'),
                    text=f"<b>ℹ️ Сервисные сообщения</b>"
                         f"\n\nВы создали новую персональную тренировку. Отправьте ссылку на неё ученику. "
                         f"\n\n<b>{work.name}</b>"
                         f"\nhttps://t.me/{getenv('BOT_NAME')}?start=work_{work.identificator}"
                )

                page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        value=f"Ссылка на тренировку отправлена в Telegram",
                        size=16
                    ),
                    duration=1500
                )
                page.snack_bar.open = True
                page.update()
                open_new_work_list()

            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        value=f"В базе данных не хватает вопросов",
                        size=16
                    ),
                    duration=1500
                )
                page.snack_bar.open = True
                page.update()


        else:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    value="Добавьте минимум 2 тега",
                    size=16
                ),
                duration=1500
            )
            page.snack_bar.open = True
            page.update()

    def generate_new_topic_work():
        data = page.session.get("new_topic_work_config")
        name = data['name']
        questions = data['questions']

        all_questions_list = get_all_questions()

        if questions.keys():
            questions_ids_pool = get_random_questions(pool=all_questions_list, request_dict=questions)

            if questions_ids_pool['is_ok']:
                work = insert_new_hand_work(
                    name=name if name else f"Тренировка {datetime.now().strftime('%Y%m%d%H%M')}",
                    identificator=hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:6],
                    questions_ids_list=questions_ids_pool['detail']
                )

                bot.send_message(
                    chat_id=getenv('ADMIN_ID'),
                    text=f"<b>ℹ️ Сервисные сообщения</b>"
                         f"\n\nВы создали новую персональную тренировку. Отправьте ссылку на неё ученику. "
                         f"\n\n<b>{work.name}</b>"
                         f"\nhttps://t.me/{getenv('BOT_NAME')}?start=work_{work.identificator}"
                )

                page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        value=f"Ссылка на тренировку отправлена в Telegram",
                        size=16
                    ),
                    duration=1500
                )
                page.snack_bar.open = True
                page.update()
                open_new_work_list()

            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        value=f"Не хватает вопросов с тегом {questions_ids_pool['tag']}",
                        size=16
                    ),
                    duration=1500
                )
                page.snack_bar.open = True
                page.update()
        else:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    value="Добавьте хотя бы один вопрос",
                    size=16
                ),
                duration=1500
            )
            page.snack_bar.open = True
            page.update()

    def update_hard_tags_list(e: ft.ControlEvent):
        # data = page.session.get('hard_tags_list')
        data = page.session.get("new_topic_work_config")

        e.control.data = e.control.data.strip()

        if e.control.value:
            if data is not None:
                data['questions'][e.control.data] = e.control.value

            else:
                data = {'name': None, 'questions': {e.control.data: e.control.value}}

        else:
            try:
                data['questions'].pop(e.control.data)
            except Exception as e:
                pass

        page.session.set('new_topic_work_config', data)

        print(page.session.get("new_topic_work_config"))

    def open_hard_tags_list_filter_work():
        page.controls.clear()
        page.appbar.actions.clear()
        switch_loading(True)

        page.session.remove('new_topic_work_config')

        main_col = ft.Column(
            controls=[
                ft.Container(
                    content=ft.TextField(
                        label="Название тренировки",
                        hint_text="Введите название тренировки",
                        on_change=change_new_work_name,
                        width=700
                    ),
                    padding=ft.padding.only(top=15)
                ),
                ft.TextField(
                    label="Количество вопросов",
                    hint_text="Введите количество вопросов",
                    value="10",
                    on_change=change_new_work_questions_count,
                    width=700
                ),
                ft.Divider(thickness=1)
            ],
            width=700
        )

        for i in range(5):
            main_col.controls.append(
                ft.TextField(
                    label=f"Тег №{i + 1}",
                    hint_text=f"Введите тег №{i + 1}",
                    data=i + 1,
                    on_change=update_hard_tags_list
                )
            )

        main_col.controls.append(
            ft.ElevatedButton(
                text="Создать тренировку",
                on_click=lambda _: generate_new_topic_work_with_hard_tags_filter()
            )
        )

        page.add(main_col)
        switch_loading(False)

    def open_new_work_list():
        page.controls.clear()
        switch_loading(True)

        parsed_topics = {}
        data = get_topics_table()
        for el in data:
            if el.volume not in parsed_topics.keys():
                parsed_topics[el.volume] = []

            parsed_topics[el.volume].append(
                {'topic_name': el.name, 'tags_list': [tag for tag in el.tags_list if 'ege' not in tag]})

        # main_col = ft.Column(
        #     controls=[
        #         ft.Container(
        #             content=ft.TextField(
        #                 label="Название",
        #                 hint_text="Введите название тренировки",
        #                 on_change=change_new_work_name,
        #             ),
        #             padding=ft.padding.only(top=15)
        #         )
        #     ],
        #     # width=700
        # )

        main_col = ft.ResponsiveRow(columns=4)

        for volume, data in parsed_topics.items():

            topic_col = ft.Column(
                controls=[
                    ft.Text(value=volume, size=20)
                ]
            )
            for topic in data:
                tags_col = ft.Column(
                    controls=[
                        ft.Text(value=topic['topic_name'], size=18),
                    ]
                )

                for tag in sorted(topic['tags_list']):
                    tags_col.controls.append(
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.ListTile(
                                        leading=ft.Icon(ft.icons.TOPIC),
                                        title=ft.Text(tag),
                                    ),
                                    expand=True,
                                ),
                                ft.TextField(
                                    width=50,
                                    value='0',
                                    on_change=change_count_of_questions,
                                    data={
                                        'tag': tag
                                    },
                                    text_align=ft.TextAlign.CENTER,
                                )
                            ]
                        )
                    )

                topic_col.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=tags_col,
                            padding=15
                        ),
                        width=700,
                        elevation=10
                    )
                )
                # print("TOPIC:", topic['topic_name'])
                # print("TAGS:", topic['tags_list'])
                # print()

            main_col.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=topic_col,
                        padding=15,
                    ),
                    width=700,
                    col={'lg': 1}
                )
            )

        # tags_list = get_all_tags()

        # tags_list = [el for el in list(set(chain.from_iterable(tags_list))) if 'ege' not in el]
        # tags_list.sort(key=lambda el: el)

        # for tag in tags_list:
        #     col.controls.append(
        #         ft.Container(
        #             ft.Row(
        #                 controls=[
        #                     ft.Container(
        #                         content=ft.ListTile(
        #                             leading=ft.Icon(ft.icons.TOPIC),
        #                             title=ft.Text(tag),
        #                         ),
        #                         expand=True,
        #                     ),
        #                     ft.TextField(
        #                         width=50,
        #                         value='0',
        #                         on_change=change_count_of_questions,
        #                         data={
        #                             'tag': tag
        #                         },
        #                         text_align=ft.TextAlign.CENTER,
        #                     )
        #                 ]
        #             ),
        #             padding=ft.padding.only(right=15)
        #         )
        #     )
        #     # col.controls.append(ft.Divider(thickness=1))

        page.appbar = ft.AppBar(
            title=ft.Text("Создание тренировки", size=18),
            actions=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.FILTER_ALT,
                                on_click=lambda _: open_hard_tags_list_filter_work()
                            ),
                            ft.IconButton(
                                icon=ft.icons.SEND,
                                on_click=lambda _: generate_new_topic_work()
                            )
                        ]
                    ),
                    padding=ft.padding.only(right=15)
                )
            ],
            bgcolor=ft.colors.SURFACE_VARIANT
        )

        page.add(
            ft.Container(
                content=ft.TextField(
                    label="Название тренировки",
                    hint_text="Введите название тренировки",
                    on_change=change_new_work_name,
                    width=700
                ),
                padding=ft.padding.only(top=15)
            )
        )
        page.add(main_col)
        switch_loading(False)

    def open_users_list():
        page.controls.clear()
        switch_loading(True)

        users = get_all_users()

        col = ft.Column(
            width=600
        )
        page.scroll = ft.ScrollMode.AUTO
        for user in users:
            col.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.ListTile(
                                        leading=ft.Icon(ft.icons.ACCOUNT_CIRCLE),
                                        title=ft.Text(user.name),
                                        subtitle=ft.Text(f"id{user.telegram_id}"),
                                    ),
                                    # padding=ft.padding.only(left=-15),
                                    expand=True,
                                    # bgcolor=ft.colors.RED
                                ),
                                ft.IconButton(
                                    icon=ft.icons.KEYBOARD_ARROW_RIGHT,
                                    data=user,
                                    on_click=open_user_info,
                                    tooltip="Профиль пользователя"
                                ),
                            ]
                        ),
                        padding=ft.padding.only(right=15)
                    )
                )
            )

        page.appbar = ft.AppBar(
            title=ft.Text("Статистика учеников", size=18),
            bgcolor=ft.colors.SURFACE_VARIANT
        )

        page.add(col)
        switch_loading(False)

    def process_remove_user(e: ft.ControlEvent):
        tid = e.control.data
        remove_user(telegram_id=tid)

        page.snack_bar = ft.SnackBar(
            content=ft.Text(
                value=f"Пользователь удалён",
                size=16
            ),
            duration=1500
        )
        page.snack_bar.open = True
        open_users_list()


    def open_user_info(e: ft.ControlEvent):
        page.controls.clear()
        switch_loading(True)

        user = e.control.data
        stats = get_user_statistics(user.telegram_id)

        col = ft.Column(
            width=600
        )

        if stats:
            page.scroll = ft.ScrollMode.AUTO
            for el in stats:
                col.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.ListTile(
                                            leading=ft.Icon(ft.icons.TOPIC),
                                            title=ft.Text(el['general']['name']),
                                            subtitle=ft.Text(
                                                f"{el['general']['time']['end'].strftime('%d.%m.%Y в %H:%M')}"),
                                        ),
                                        # padding=ft.padding.only(left=-15),
                                        expand=True
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.KEYBOARD_ARROW_RIGHT,
                                        url=f"{getenv('STATS_HOST')}/student/view-stats?uuid={user.id}&tid={user.telegram_id}&work={el['general']['work_id']}&detailed=1",
                                        tooltip="Перейти к статистике",
                                    ),
                                ]
                            ),
                            padding=ft.padding.only(right=15)
                        )
                    )
                )

        else:
            page.scroll = None
            page.horizontal_alignment = "center"
            page.add(
                get_info_column(
                    caption="Завершённых тренировок пока нет",
                    icon_filename="tubes.png"
                )
            )

        page.appbar = ft.AppBar(
            title=ft.Text(user.name, size=18),
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=lambda _: open_users_list()
            ),
            actions=[
                ft.Container(
                    content=ft.ElevatedButton(
                        icon=ft.icons.NO_ACCOUNTS,
                        text="Удалить ученика",
                        on_long_press=process_remove_user,
                        data=user.telegram_id
                    ),
                    padding=ft.padding.only(right=15)
                )
            ],
        )

        page.add(col)
        switch_loading(False)

    def change_ege_mark(e: ft.ControlEvent):
        config = page.session.get("ege_converting_config")

        if e.control.value.isnumeric() and 100 >= int(e.control.value) >= 1:
            config[e.control.data]['value'] = int(e.control.value)
            config[e.control.data]['is_ok'] = True
            e.control.border_color = ft.colors.GREEN

        else:
            config[e.control.data]['value'] = e.control.value
            config[e.control.data]['is_ok'] = False
            e.control.border_color = ft.colors.RED

        page.update()

        page.session.set("ege_converting_config", config)

    def update_ege_marks_list():
        config = page.session.get("ege_converting_config")

        if all([el['is_ok'] for el in config.values()]):
            page.controls.clear()
            switch_loading(True)

            update_ege_converting(config)

            # info_dialog.title.value = "Обновление данных"
            # info_dialog.content.value = "Данные "
            page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    value=f"Данные успешно обновлены",
                    size=16
                ),
                duration=1500
            )
            page.snack_bar.open = True
            open_ege_marks_list()

        else:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    value=f"Исправьте ошибки в данных",
                    size=16
                ),
                duration=1500
            )
            page.snack_bar.open = True
            page.update()

    def open_ege_marks_list():
        page.controls.clear()
        switch_loading(True)
        data = get_ege_converting()

        config = {}

        col = ft.Column(
            width=600,
            horizontal_alignment="center"
        )

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Первичный", size=18), numeric=False, heading_row_alignment="center"),
                ft.DataColumn(ft.Text("Вторичный", size=18), heading_row_alignment="center"),
            ],
            border=ft.border.all(1, "white"),
            vertical_lines=ft.BorderSide(1, "white"),
            horizontal_lines=ft.BorderSide(1, "white"),
            width=400,
            data_row_min_height=50,
        )
        col.controls.append(table)

        for el in data:
            config[el.input_mark] = {'value': el.output_mark, 'is_ok': True}
            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(el.input_mark), size=16)),
                        ft.DataCell(
                            ft.TextField(
                                border_width=3,
                                value=str(el.output_mark),
                                text_align=ft.TextAlign.CENTER,
                                expand=True,
                                # border=ft.InputBorder.UNDERLINE,
                                data=el.input_mark,
                                on_change=change_ege_mark
                            )
                        ),
                    ],
                )
            )

        page.session.set("ege_converting_config", config)

        page.appbar = ft.AppBar(
            title=ft.Text("Конвертация баллов ЕГЭ", size=18),
            actions=[
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.icons.SAVE,
                        on_click=lambda _: update_ege_marks_list()
                    ),
                    padding=ft.padding.only(right=15)
                )
            ],
            bgcolor=ft.colors.SURFACE_VARIANT
        )

        page.add(col)
        switch_loading(False)

    # def check_question_card_after_update_btn(e: ft.ControlEvent):
    #     id = e.control.value
    #     data = page.session.get("")

    def validate_question_card(e: ft.ControlEvent):
        question_data = page.session.get('currrent_question_data')
        data = e.control.data
        place = data['place']
        arg = data['arg']
        field_value = str(e.control.value).strip()

        wrong_fields = []

        if place in ["question_field", "answer_field"]:
            if len(field_value) < 1:
                e.control.border_color = ft.colors.RED
            else:
                e.control.border_color = ft.colors.GREEN
                setattr(question_data, arg, field_value)

        elif place in ["level_field", "mark_field"]:
            e.control.border_color = ft.colors.GREEN
            setattr(question_data, arg, int(field_value))
            # if len(field_value) == 1 and field_value.isnumeric() and 0 < int(field_value) <= 5:
            #     e.control.border_color = ft.colors.GREEN
            #     setattr(question_data, arg, int(field_value))
            # else:
            #     e.control.border_color = ft.colors.RED
            #     wrong_fields.append(place)

        elif place == "tags_list_field":
            if len(field_value.split("\n")) > 0 and field_value.split("\n")[0] != "":
                e.control.border_color = ft.colors.GREEN
                setattr(question_data, arg, field_value.split("\n"))
            else:
                e.control.border_color = ft.colors.RED
                wrong_fields.append(place)

        elif place in ['rotate', 'selfcheck']:
            setattr(question_data, arg, int(e.control.value))

        page.session.set('currrent_question_data', question_data)
        page.update()

    # def goto_query(e: ft.ControlEvent):
    #     open_pool_list(
    #         page_num=None,
    #         query=e.control.value.strip()
    #     )

    info_dialog = ft.AlertDialog(
        title=ft.Text(size=20),
        content=ft.Text(size=16),
        actions=[
            ft.ElevatedButton(
                text="Хорошо",
                on_click=lambda _: open_find_in_pool()
            )
        ]
    )

    page.overlay.append(info_dialog)

    def process_delete_or_update_question(e: ft.ControlEvent):
        question_data = page.session.get('currrent_question_data')
        action = e.control.data

        if action == 'remove_question':
            # todo: проверить наличие вопроса в hand_work перед удалением. Если удаляем вопрос, то удаляем всю hand_work
            deactivate_question(question_data.id)
            page.controls.clear()
            info_dialog.title.value = "Удаление вопроса"
            info_dialog.content.value = "Вопрос успешно удалён из базы!"

        elif action == 'update_question':
            update_question(question_data)
            info_dialog.title.value = "Обновление вопроса"
            info_dialog.content.value = "Содержимое вопроса успешно обновлено!"

        info_dialog.open = True
        page.update()

    def goto_update_image(e: ft.ControlEvent):
        page.session.set('upload_image_config', e.control.data)

        file_picker.pick_files(
            file_type=ft.FilePickerFileType.IMAGE,
            allowed_extensions=['png']
        )

    def goto_upload_image(e: ft.ControlEvent):
        upload_id = str(datetime.now().timestamp())
        data = e.control.data
        img_type = data['type']
        data['upload_id'] = upload_id

        gen_data = page.session.get('gen_upload_data')
        if gen_data is not None:
            gen_data[f"{img_type}_img_id"] = upload_id
            page.session.set('gen_upload_data', gen_data)
        else:
            page.session.set('gen_upload_data', {f"{img_type}_img_id": upload_id})

        print(page.session.get('gen_upload_data'))

        page.session.set('upload_new_image_config', data)

        new_file_picker.pick_files(
            file_type=ft.FilePickerFileType.IMAGE,
            allowed_extensions=['png']
        )

    def open_question_card(question_id: int):
        find_question_dialog.open = False
        page.controls.clear()
        switch_loading(True)

        el = get_question_from_pool(question_id=question_id)
        page.session.set("currrent_question_data", el)

        page.appbar.title.value = f"Карточка вопроса (id{el.id})"

        col = ft.Column(
            controls=[
                ft.Card(
                    ft.Container(
                        ft.Column(
                            [
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.TEXT_FIELDS),
                                    title=ft.TextField(
                                        label="Текст вопроса",
                                        value=el.text,
                                        multiline=True,
                                        data={'place': "question_field", "question": el, 'arg': "text"},
                                        on_change=validate_question_card
                                    ),
                                ),
                                ft.Container(
                                    content=ft.ListTile(
                                        leading=ft.IconButton(
                                            icon=ft.icons.IMAGE,
                                            tooltip="Обновить изображение вопроса",
                                            on_click=goto_update_image,
                                            data={'type': 'question', 'id': el.id}
                                        ),
                                        title=ft.Column([
                                            ft.Image(
                                                src_base64=image_to_base64("question", el.id),
                                                error_content=ft.Text("Ошибка загрузки изображения"),
                                            ) if el.question_image else ft.Text("Изображение отсутствует")
                                        ]),
                                        subtitle=ft.Text("изображение вопроса"),
                                    ),
                                    padding=ft.padding.only(left=-10)
                                ),
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.INFO),
                                    title=ft.OutlinedButton(
                                        text="Удалить изображение",
                                        icon=ft.icons.DELETE,
                                        disabled=False if bool(el.question_image) else True,
                                        on_long_press=remove_image_from_question,
                                        data={'type': 'question', 'id': el.id}

                                    ),
                                ),
                            ]
                        ),
                        padding=15
                    )
                ),
                ft.Card(
                    ft.Container(
                        ft.Column(
                            [
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.TEXT_FIELDS),
                                    title=ft.TextField(
                                        label="Текст ответа",
                                        value=el.answer,
                                        multiline=True,
                                        data={'place': "answer_field", "question": el, 'arg': "answer"},
                                        on_change=validate_question_card
                                    ),
                                    # subtitle=ft.Text("текст ответа")
                                ),
                                ft.Container(
                                    content=ft.ListTile(
                                        leading=ft.IconButton(
                                            icon=ft.icons.IMAGE,
                                            tooltip="Обновить изображение ответа",
                                            on_click=goto_update_image,
                                            data={'type': 'answer', 'id': el.id}
                                        ),
                                        title=ft.Column([
                                            ft.Image(
                                                src_base64=image_to_base64("answer", el.id),
                                                error_content=ft.Text("Ошибка загрузки изображения"),
                                            ) if el.answer_image else ft.Text("Изображение отсутствует")
                                        ]),
                                        subtitle=ft.Text("изображение ответа"),
                                    ),
                                    padding=ft.padding.only(left=-10)
                                ),
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.INFO),
                                    title=ft.OutlinedButton(
                                        text="Удалить изображение",
                                        icon=ft.icons.DELETE,
                                        disabled=False if bool(el.answer_image) else True,
                                        on_long_press=remove_image_from_question,
                                        data={'type': 'answer', 'id': el.id}
                                    ),
                                ),
                            ]
                        ),
                        padding=15
                    )
                ),
                ft.Card(
                    ft.Container(
                        ft.Column(
                            [
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.CALCULATE),
                                    title=ft.Dropdown(
                                        label="Уровень сложности",
                                        value=str(el.level),
                                        options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in range(1, 6)],
                                        data={'place': "level_field", "question": el, 'arg': "level"},
                                        on_change=validate_question_card
                                    )
                                ),
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.BAR_CHART),
                                    title=ft.Dropdown(
                                        label="Максимальный балл",
                                        value=str(el.full_mark),
                                        options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in range(1, 6)],
                                        data={'place': "mark_field", "question": el, 'arg': "full_mark"},
                                        on_change=validate_question_card
                                    )
                                ),
                                # ft.ListTile(
                                #     leading=ft.Icon(ft.icons.NUMBERS),
                                #     title=ft.TextField(
                                #         label="Максимальный балл",
                                #         value=str(el.full_mark),
                                #         multiline=True,
                                #         data={'place': "mark_field", "question": el, 'arg': "full_mark"},
                                #         on_change=validate_question_card
                                #     ),
                                #     # subtitle=ft.Text("максимальный балл")
                                # ),
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.NUMBERS),
                                    title=ft.TextField(
                                        label="Список тегов",
                                        value="\n".join(a for a in el.tags_list),
                                        multiline=True,
                                        data={'place': "tags_list_field", "question": el, 'arg': "tags_list"},
                                        on_change=validate_question_card
                                    ),
                                    # subtitle=ft.Text("список тегов"),
                                ),
                            ]
                        ),
                        padding=15
                    )
                ),
                ft.Card(
                    ft.Container(
                        ft.Column(
                            [
                                ft.ListTile(
                                    leading=ft.Switch(value=bool(el.is_rotate),
                                                      on_change=validate_question_card,
                                                      data={'place': "rotate", "question": el, 'arg': "is_rotate"}),
                                    title=ft.Text("Вращение ответа", size=16)
                                ),
                                ft.ListTile(
                                    leading=ft.Switch(value=bool(el.is_rotate),
                                                      on_change=validate_question_card,
                                                      data={'place': "selfcheck", "question": el,
                                                            'arg': "is_selfcheck"}),
                                    title=ft.Text("Самопроверка", size=16)
                                ),
                                # ft.Switch(label="Вращение ответа", value=bool(el.is_rotate),
                                #           on_change=validate_question_card,
                                #           data={'place': "rotate", "question": el, 'arg': "is_rotate"}),
                                # ft.Switch(label="Самопроверка", value=bool(el.is_selfcheck),
                                #           on_change=validate_question_card,
                                #           data={'place': "selfcheck", "question": el, 'arg': "is_selfcheck"}),
                            ]
                        )
                    )
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.OutlinedButton(
                            icon=ft.icons.DELETE,
                            text="Удалить впорос",
                            data='remove_question',
                            on_long_press=process_delete_or_update_question
                        ),
                        ft.ElevatedButton(
                            icon=ft.icons.SAVE,
                            text="Сохранить",
                            data='update_question',
                            on_click=process_delete_or_update_question
                        )
                    ],
                )
            ],
            horizontal_alignment="center",
            width=800
        )

        page.add(col)
        switch_loading(False)

    def process_edit_find_question_dialog(e: ft.ControlEvent):
        action = e.control.data

        questions_ids_list = page.session.get('questions_ids_list')

        if action == "update_value":
            user_input = str(e.control.value)

            if user_input.isnumeric() and int(user_input) in questions_ids_list:
                page.session.set("question_id_for_find", e.control.value)
                find_question_dialog.content.controls[1].value = ""
                find_question_dialog.actions[0].disabled = False
            else:
                find_question_dialog.content.controls[1].value = "Неверный формат ID / ID не существует"
                find_question_dialog.actions[0].disabled = True


        elif action == "find_question":
            find_question_dialog.content.controls[0].value = None
            find_question_dialog.actions[0].disabled = True

            question_id = int(page.session.get("question_id_for_find"))
            open_question_card(question_id=question_id)

        page.update()

    find_question_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Пул вопросов", size=20),
        content=ft.Column(
            controls=[
                ft.TextField(
                    label="ID вопроса",
                    on_change=process_edit_find_question_dialog,
                    data='update_value'
                ),
                ft.Text(size=16)
            ],
            width=600,
            height=50
        ),
        actions=[
            ft.ElevatedButton(
                text="Перейти к вопросу",
                icon=ft.icons.FILE_OPEN,
                on_click=process_edit_find_question_dialog,
                data='find_question',
                disabled=True
            )
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )

    page.overlay.append(find_question_dialog)

    def open_find_in_pool():
        page.controls.clear()

        page.appbar = ft.AppBar(
            title=ft.Text(page.title, size=18),
            bgcolor=ft.colors.SURFACE_VARIANT
        )

        pool = get_all_pool(active=True)
        questions_ids_list = [el.id for el in pool]
        page.session.set('questions_ids_list', questions_ids_list)
        find_question_dialog.open = True

        page.update()

    def edit_new_q_config(e: ft.ControlEvent):
        config = page.session.get('gen_upload_data')

        if config is not None:
            data = config
        else:
            data = {}

        el = e.control.data

        if el == "q_selfcheck":
            data['is_selfcheck'] = e.control.value

        elif el == "q_rotate":
            data['is_rotate'] = e.control.value

        elif el == "q_type":
            if e.control.value == 'КИМ ЕГЭ':
                data['type'] = 'ege'
            elif e.control.value == 'Тема':
                data['type'] = 'topic'

        elif el == "q_full_mark":
            data['full_mark'] = int(e.control.value)

        elif el == "q_level":
            data['level'] = int(e.control.value)

        elif el == "q_question":
            data['question'] = e.control.value

        elif el == "q_answer":
            data['answer'] = e.control.value

        elif el == "q_tags_list":
            data['tags_list'] = [el.lower().replace('ё', 'е') for el in e.control.value.split("\n") if el]

        page.session.set('gen_upload_data', data)

        print(page.session.get('gen_upload_data'))

    def save_new_question(e: ft.ControlEvent):
        data = page.session.get('gen_upload_data')

        values_names = ['question', 'answer', 'type', 'level', 'full_mark', 'tags_list']
        if all([el in data.keys() for el in values_names]):
            pool = Pool(
                text=data['question'],
                answer=data['answer'],
                type=data['type'],
                level=data['level'],
                full_mark=data['full_mark'],
                tags_list=data['tags_list'],
                question_image=0,
                answer_image=0,
                is_selfcheck=data['is_selfcheck'],
                is_rotate=data['is_rotate'],
            )

            if data['q_img']['uploaded']:
                pool.question_image = 1

            if data['a_img']['uploaded']:
                pool.answer_image = 1

            question = insert_question_into_pool(pool)

            if data['q_img']['uploaded']:
                move_image(
                    source_path=f"{getenv('ROOT_FOLDER')}/data/temp/{data['q_img']['id']}.png",
                    destination_path=f"{getenv('ROOT_FOLDER')}/data/questions_images/{question.id}.png",
                )

            if data['a_img']['uploaded']:
                move_image(
                    source_path=f"{getenv('ROOT_FOLDER')}/data/temp/{data['a_img']['id']}.png",
                    destination_path=f"{getenv('ROOT_FOLDER')}/data/answers_images/{question.id}.png",
                )

            page.session.remove('gen_upload_data')
            upload_question_image_col.controls.clear()
            upload_answer_image_col.controls.clear()
            navigate()
            dlg = ft.AlertDialog(
                title=ft.Text(page.title, size=20),
                content=ft.Text("Вопрос успешно добавлен", size=16)
            )
            page.overlay.append(dlg)
            dlg.open = True

        else:
            dlg = ft.AlertDialog(
                title=ft.Text(page.title, size=20),
                content=ft.Text("Заполните все поля!", size=16)
            )
            page.overlay.append(dlg)
            dlg.open = True
        page.update()

    def open_add_question():
        page.controls.clear()

        page.appbar = ft.AppBar(
            title=ft.Text(page.title, size=18),
            bgcolor=ft.colors.SURFACE_VARIANT
        )

        main_col = ft.ResponsiveRow(
            columns=3,
            controls=[
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Вопрос", size=18),
                                ft.TextField(
                                    prefix_icon=ft.icons.TEXT_FIELDS,
                                    label="Текст вопроса",
                                    multiline=True,
                                    data="q_question",
                                    on_change=edit_new_q_config
                                ),
                                ft.OutlinedButton(
                                    text="Загрузить изображение вопроса",
                                    icon=ft.icons.UPLOAD_FILE,
                                    on_click=goto_upload_image,
                                    data={'type': 'question'}
                                ),
                                upload_question_image_col
                            ]
                        ),
                        padding=15
                    ),
                    col={'lg': 1}
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Ответ", size=18),
                                ft.TextField(
                                    prefix_icon=ft.icons.TEXT_FIELDS,
                                    label="Текст ответа",
                                    multiline=True,
                                    data="q_answer",
                                    on_change=edit_new_q_config
                                ),
                                ft.OutlinedButton(
                                    text="Загрузить изображение ответа",
                                    icon=ft.icons.UPLOAD_FILE,
                                    on_click=goto_upload_image,
                                    data={'type': 'answer'}
                                ),
                                upload_answer_image_col
                            ]
                        ),
                        padding=15
                    ),
                    col={'lg': 1}
                ),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Параметры", size=18),
                                ft.Dropdown(
                                    label="Тип вопроса",
                                    options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in ['КИМ ЕГЭ', 'Тема']],
                                    data="q_type",
                                    on_change=edit_new_q_config
                                ),
                                ft.Dropdown(
                                    prefix_icon=ft.icons.CALCULATE,
                                    label="Уровень сложности",
                                    options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in range(1, 6)],
                                    data="q_level",
                                    on_change=edit_new_q_config
                                ),
                                ft.Dropdown(
                                    prefix_icon=ft.icons.BAR_CHART,
                                    label="Максимальный балл",
                                    options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in range(1, 6)],
                                    data="q_full_mark",
                                    on_change=edit_new_q_config
                                ),
                                ft.Divider(thickness=1),
                                ft.ListTile(
                                    leading=ft.Switch(value=False, data="q_rotate",
                                                      on_change=edit_new_q_config),
                                    title=ft.Text("Вращение ответа", size=16)
                                ),
                                ft.ListTile(
                                    leading=ft.Switch(value=False, data="q_selfcheck",
                                                      on_change=edit_new_q_config),
                                    title=ft.Text("Самопроверка", size=16)
                                ),
                                ft.Divider(thickness=1),
                                ft.TextField(
                                    label="Список тегов",
                                    multiline=True,
                                    data="q_tags_list",
                                    on_change=edit_new_q_config
                                ),
                                ft.Divider(thickness=1),
                                ft.Row([
                                    # ft.OutlinedButton(
                                    #     text="Очистить поля",
                                    #     icon=ft.icons.CLEAR_ALL
                                    # ),
                                    ft.FilledButton(
                                        text="Сохранить вопрос",
                                        icon=ft.icons.SAVE_ALT,
                                        on_click=save_new_question
                                    )
                                ])
                            ]
                        ),
                        padding=15
                    ),
                    col={'lg': 1}
                )
            ]
        )

        page.add(main_col)

    if platform.system() == "Windows":
        # page.route = "/student/view-stats?uuid=1&tid=409801981&work=40&detailed=1"
        # page.route = "/admin/create-hand-work?auth_key=develop&admin_id=develop"

        page.route = "/admin/students-stats?auth_key=develop&admin_id=develop"
        # page.route = "/admin/ege-converting?auth_key=develop&admin_id=develop"
        # page.route = "/admin/pool?auth_key=develop&admin_id=develop"
        # page.route = "/admin/add-question?auth_key=develop&admin_id=develop"

    def error_404():
        page.controls.clear()
        page.scroll = None
        page.title = "404"
        col = get_info_column("Такой страницы не существует",
                              icon_filename='error.png')
        page.add(col)

    def navigate(e=None):
        path = urlparse(page.route).path
        url_params = {key: (value[0]) for key, value in parse_qs(urlparse(page.route).query).items()}

        volume = path.split("/")[-1]
        if re.match(r"^/admin/.*", path) is not None:

            if all(key in url_params for key in ['auth_key', 'admin_id']) and get_value(url_params['admin_id']) == \
                    url_params['auth_key']:

                page.scroll = ft.ScrollMode.AUTO
                if volume == "create-hand-work":
                    page.title = "Создание тренировки"

                    page.session.set('new_topic_work_config', {'name': "", 'questions': {}})
                    open_new_work_list()

                elif volume == "students-stats":
                    page.title = "Статистика учеников"
                    open_users_list()

                elif volume == "ege-converting":
                    page.title = "Конвертация баллов ЕГЭ"

                    open_ege_marks_list()

                elif volume == "pool":
                    page.title = "Пул вопросов"
                    open_find_in_pool()

                elif volume == "add-question":
                    page.title = "Добавление вопросов"
                    page.session.set('gen_upload_data', {'is_rotate': False, 'is_selfcheck': False,
                                                         'a_img': {'uploaded': False, 'id': None},
                                                         'q_img': {'uploaded': False, 'id': None}})
                    open_add_question()

                else:
                    error_404()

            elif 'update_question_id' in url_params:
                open_question_card(question_id=int(url_params['update_question_id']))

            else:
                page.controls.clear()
                col = get_info_column("Время действия ключа авторизации истекло, вызовите /admin ещё раз",
                                      icon_filename='error.png')
                page.add(col)

        elif re.match(r"^/student/.*", path) is not None:
            if all(key in url_params for key in ['uuid', 'tid', 'work']) and get_work_by_url_data(url_params['uuid'],
                                                                                                  url_params['tid'],
                                                                                                  url_params['work']):
                if volume == "view-stats":
                    page.title = "Результат тренировки"
                    col = get_info_column("Загружаем информацию", progress_bar_visible=True,
                                          icon_filename='loading.png')
                    page.add(col)

                    page.scroll = ft.ScrollMode.AUTO

                    all_stats = get_user_statistics(int(url_params['tid']))
                    work_stats = [s for s in all_stats if s['general']['work_id'] == int(url_params['work'])][-1]
                    questions_list = get_work_questions_joined_pool(int(url_params['work']))

                    detailed = False
                    if 'detailed' in url_params:
                        detailed = bool(url_params['detailed'])

                    main_col = ft.Column(
                        controls=[
                            get_general_info_card(work_stats, detailed=detailed),
                            get_questions_info_card(questions_list, detailed=detailed)
                        ],
                        width=700
                    )

                    page.controls = [main_col]
                    page.update()

                else:
                    error_404()

            else:
                page.controls.clear()
                col = get_info_column("Ничего не нашлось, попробуй ещё раз или обратись в поддержку через /feedback",
                                      icon_filename='error.png')
                page.add(col)

        else:
            error_404()

    page.on_connect = navigate
    navigate()


if __name__ == "__main__":
    os.environ["FLET_SECRET_KEY"] = os.urandom(12).hex()
    ft.app(
        target=main,
        assets_dir=os.path.join(getenv('ROOT_FOLDER'), "flet_apps/assets"),
        upload_dir=os.path.join(getenv('ROOT_FOLDER'), "data/uploads"),
        view=ft.AppView.WEB_BROWSER,
        port=6002
    )
