import sys
import os
import time
from typing import List

from redis_db.crud import get_value
from utils.image_converter import image_to_base64

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from os import getenv
from urllib.parse import urlparse, parse_qs
import flet as ft
from utils.user_statistics import get_user_statistics
from db.crud import get_work_by_url_data, get_work_questions_joined_pool, get_user, get_all_users
from db.models import Work, WorkQuestion, User
from dotenv import load_dotenv

load_dotenv()


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

    def open_users_list():
        page.controls.clear()
        switch_loading(True)

        users = get_all_users()

        col = ft.Column(
            width=600
        )
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

        page.add(col)
        switch_loading(False)

    def open_user_info(e: ft.ControlEvent):
        page.controls.clear()
        switch_loading(True)

        user = e.control.data
        stats = get_user_statistics(user.telegram_id)

        col = ft.Column(
            controls=[
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    ft.IconButton(
                                        icon=ft.icons.KEYBOARD_ARROW_LEFT,
                                        tooltip="Назад",
                                        on_click=lambda _: open_users_list()
                                    ),
                                    # padding=ft.padding.only(left=-15)
                                ),
                                ft.Container(
                                    content=ft.ListTile(
                                        leading=ft.Icon(ft.icons.ACCOUNT_CIRCLE),
                                        title=ft.Text(user.name),
                                        subtitle=ft.Text(f"всего тренировок: {len(stats)}"),
                                    ),
                                    padding=ft.padding.only(left=-15),
                                    expand=True
                                )
                            ]
                        ),
                        padding=ft.padding.only(left=15)
                    )
                ),
                ft.Divider(thickness=1)
            ],
            width=600
        )

        if stats:
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
                                        padding=ft.padding.only(left=-15),
                                        expand=True
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.KEYBOARD_ARROW_RIGHT,
                                        url=f"{getenv('STATS_HOST')}/stats?uuid={user.id}&tid={user.telegram_id}&work={el['general']['work_id']}&detailed=1",
                                        tooltip="Перейти к статистике",
                                    ),
                                ]
                            ),
                            padding=15
                        )
                    )
                )

        else:
            col.controls.append(
                ft.Column(
                    alignment="center",
                    horizontal_alignment="center",
                    controls=[
                        ft.Image(
                            src=f"/images/tubes.png",
                            error_content=ft.Icon(ft.icons.ERROR, size=50),
                            height=120
                        ),
                        ft.Text("Завершённых тренировок пока нет", size=16)
                    ],
                    width=600
                )
            )

        page.add(col)
        switch_loading(False)

    # page.route = "/stats?uuid=1&tid=409801981&work=11"
    # page.route = "/stats?uuid=1&tid=409801981&work=11&detailed=1"
    # page.route = "/stats?auth_key=1ede7cee14d32e1fb1b258ae669c17ef1c6e9aaa4b294b9746fa1aa61a36efda&admin_id=409801981"

    url_params = {key: (value[0]) for key, value in parse_qs(urlparse(page.route).query).items()}

    print(get_value(url_params['admin_id']))
    if all(key in url_params for key in ['uuid', 'tid', 'work']) and get_work_by_url_data(url_params['uuid'],
                                                                                          url_params['tid'],
                                                                                          url_params['work']):
        col = get_info_column("Загружаем информацию", progress_bar_visible=True, icon_filename='loading.png')
        page.add(col)
        time.sleep(1)

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


    elif all(key in url_params for key in ['auth_key', 'admin_id']) and get_value(url_params['admin_id']) == url_params['auth_key']:
        page.scroll = ft.ScrollMode.AUTO
        open_users_list()

    else:
        col = get_info_column("Ничего не нашлось, попробуй ещё раз или обратись в поддержку через /feedback",
                              icon_filename='error.png')
        page.add(col)


if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir=os.path.join(getenv('ROOT_FOLDER'), "flet_apps/assets"),
        view=ft.AppView.WEB_BROWSER,
        port=6002
    )
