from os import getenv

import flet as ft

from db.models import Work, User
from flet_apps.control.columns.error import get_error_col


def get_user_info_col(user: User, works: list, page: ft.Page) -> ft.Column:
    """
    Создание column для страницы с информацией о пользователе
    :param user: данные о пользователе из БД (db.models.User)
    :param works: List с информацией о выполненных заданиях
    :return:
    """
    works_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text(
                                    value="История тренировок",
                                    size=20
                                )
                            ]
                        ),
                        padding=ft.padding.only(bottom=10)
                    )
                ],
                horizontal_alignment="center"
            ),
            padding=15
        ),
        width=600
    )

    if works:
        for work in works:
            works_card.content.content.controls.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.ListTile(
                                leading=ft.Icon(ft.icons.NEWSPAPER),
                                title=ft.Text(work['general']['name']),
                                subtitle=ft.Text(f"{work['general']['time']['end'].strftime('%d.%m.%Y в %H:%M')}"),
                            ),
                            padding=ft.padding.only(left=-15, bottom=0),
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.icons.KEYBOARD_ARROW_RIGHT,
                                url=f"{getenv('STATS_HOST')}/stats?uuid={user.id}&tid={user.telegram_id}&work={work['general']['work_id']}&detailed=1",
                                data=user
                            ),
                            padding=ft.padding.only(right=10)
                        )

                    ]
                )

            )
    else:
        works_card.content.content.controls.append(
            get_error_col(page, "Выполненных тренировок пока нет", disable_scroll=False, icon_filename="tubes.png")
        )

    col = ft.Column(
        controls=[
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                value="Данные профиля",
                                size=20
                            ),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.ListTile(
                                            leading=ft.Icon(ft.icons.ACCOUNT_CIRCLE),
                                            title=ft.Text(user.name),
                                            subtitle=ft.Text(f"id{user.telegram_id}"),
                                        ),
                                        padding=ft.padding.only(left=-15, bottom=0)
                                    ),

                                ]
                            )
                        ]
                    ),
                    padding=15
                ),
                width=600
            ),
            works_card
        ]
    )

    return col
