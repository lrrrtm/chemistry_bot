from typing import List

import flet as ft

from db.models import User


def get_users_col(users: List[User], after_user_btn_clicked) -> ft.Column:
    """
    Создание column для страницы со списком пользователей
    :param users: List[User] с информацией о пользователях 
    :param after_user_btn_clicked: действие при нажатии кнопки перехода к пользователю
    :return: 
    """
    col = ft.Column()

    # for user in users:
    #     col.controls.append(
    #         ft.Card(
    #             content=ft.Container(
    #                 content=ft.Row(
    #                     controls=[
    #                         # ft.Container(
    #                         #     content=ft.ListTile(
    #                         #         leading=ft.Icon(ft.icons.ACCOUNT_CIRCLE),
    #                         #         title=ft.Text(user.name),
    #                         #         subtitle=ft.Text(f"id{user.telegram_id}"),
    #                         #     ),
    #                         #     expand=True,
    #                         # ),
    #                         ft.Container(
    #                             content=ft.IconButton(
    #                                 icon=ft.icons.KEYBOARD_ARROW_RIGHT,
    #                                 on_click=after_user_btn_clicked,
    #                                 data=user
    #                             ),
    #                             padding=ft.padding.only(right=10)
    #                         )
    #                     ]
    #                 ),
    #                 padding=10
    #             ),
    #             width=600
    #         )
    #     )

    for user in users:
        col.controls.append(
            ft.Text(f"len(users): {len(users)}", size=16)
            # ft.Card(
            #     content=ft.Column(
            #         controls=[
            #             ft.Text(user.name),
            #             ft.ElevatedButton(
            #                 text="Открыть",
            #                 data=user,
            #                 on_click=after_user_btn_clicked,
            #             )
            #         ]
            #     ),
            #     width=600
            # )
        )

    return col
