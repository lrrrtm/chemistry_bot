import hashlib
import re
import sys
import os
from datetime import datetime
from itertools import chain
from typing import List

import telebot

from redis_db.crud import get_value, set_temporary_key
from utils.image_converter import image_to_base64
from utils.tags_helper import get_random_questions

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from os import getenv
from urllib.parse import urlparse, parse_qs
import flet as ft
from utils.user_statistics import get_user_statistics
from db.crud import get_work_by_url_data, get_work_questions_joined_pool, get_all_users, get_all_tags, \
    get_all_questions, insert_new_hand_work, get_ege_converting, update_ege_converting
from db.models import WorkQuestion
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(token=getenv('BOT_API_KEY'), parse_mode='html')


# set_temporary_key(
#     'develop',
#     'develop',
#     3600
# )


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
                                [ft.Icon(ft.icons.CIRCLE, color=card_color), ft.Text(f"№ {index + 1}", size=18)]),
                                padding=ft.padding.only(left=10, top=10)),
                            ft.Image(
                                src_base64=image_to_base64(
                                    question.question_id) if bool(question.question_image) else None,
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

    def switch_loading(value: bool):
        loading_bar.visible = value

        page.update()

    def change_new_work_name(e: ft.ControlEvent):
        config = page.session.get("new_topic_work_config")

        config['name'] = e.control.value

        page.session.set(
            "new_topic_work_config",
            config,
        )

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
            questions.pop(tag)

        config['questions'] = questions
        page.session.set(
            "new_topic_work_config",
            config,
        )

    def generate_new_topic_work():
        data = page.session.get("new_topic_work_config")
        name = data['name']
        questions = data['questions']

        all_questions_list = get_all_questions()

        if questions.keys():
            questions_ids_pool = get_random_questions(pool=all_questions_list, request_dict=questions)

            if questions_ids_pool['is_ok']:
                work = insert_new_hand_work(
                    name=name if name else f"Тренировка {datetime.now().date()}",
                    identificator=hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:6],
                    questions_ids_list=questions_ids_pool['detail']
                )

                bot.send_message(
                    chat_id=getenv('FBACK_GROUP_ID'),
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

    def open_new_work_list():
        page.controls.clear()
        switch_loading(True)

        tags_list = get_all_tags()

        tags_list = [el for el in list(set(chain.from_iterable(tags_list))) if 'ege' not in el]
        tags_list.sort(key=lambda el: el)

        col = ft.Column(
            controls=[
                ft.Container(
                    content=ft.TextField(
                        label="Название",
                        hint_text="Введите название тренировки",
                        on_change=change_new_work_name,
                    ),
                    padding=ft.padding.only(top=15)
                )
            ],
            width=600
        )
        for tag in tags_list:
            col.controls.append(
                ft.Container(
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
                    ),
                    padding=ft.padding.only(right=15)
                )
            )
            # col.controls.append(ft.Divider(thickness=1))

        page.appbar = ft.AppBar(
            title=ft.Text("Создание тренировки", size=18),
            actions=[
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.icons.SEND,
                        on_click=lambda _: generate_new_topic_work()
                    ),
                    padding=ft.padding.only(right=15)
                )
            ],
            bgcolor=ft.colors.SURFACE_VARIANT
        )

        page.add(col)
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
            )
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

    # page.route = "/student/view-stats?uuid=1&tid=409801981&work=40&detailed=1"
    # page.route = "/admin/create-hand-work?auth_key=develop&admin_id=develop"
    # page.route = "/admin/students-stats?auth_key=develop&admin_id=develop"
    # page.route = "/admin/ege-converting?auth_key=develop&admin_id=develop"

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

                else:
                    error_404()

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
    ft.app(
        target=main,
        assets_dir=os.path.join(getenv('ROOT_FOLDER'), "flet_apps/assets"),
        view=ft.AppView.WEB_BROWSER,
        port=6002
    )
