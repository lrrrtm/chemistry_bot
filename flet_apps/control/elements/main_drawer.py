from math import pi

import flet as ft


def get_main_drawer(on_drawer_el_selected) -> ft.NavigationDrawer:
    """
    Создание основного drawer с элементами меню
    :param on_drawer_el_selected: действие при нажатии на элемент drawer
    :return:
    """
    return ft.NavigationDrawer(
        controls=[
            ft.Container(height=12),
            ft.ListTile(
                title=ft.Text("ХимБот", weight=ft.FontWeight.W_400, size=20),
                leading=ft.Image(src='icons/loading-animation.png', height=30)
            ),
            ft.Divider(thickness=1),

            ft.ListTile(
                title=ft.Text("Ученики"),
                leading=ft.Icon(ft.icons.GROUPS),
                data={'sec': "users", 'act': "users"},
                on_click=on_drawer_el_selected),

            ft.ExpansionTile(
                title=ft.Text("База вопросов"),
                leading=ft.Icon(ft.icons.QUESTION_MARK),
                expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.ListTile(
                        title=ft.Text("КИМ ЕГЭ"),
                        # subtitle=ft.Text("Загрузка таблицы с информацией о детях"),
                        leading=ft.Icon(ft.icons.SCHOOL),
                        data={'sec': "questions", 'act': "ege"},
                        on_click=on_drawer_el_selected),
                    ft.ListTile(
                        title=ft.Text("Тренировки"),
                        # subtitle=ft.Text("Перевод ребёнка в другую группу"),
                        leading=ft.Icon(ft.icons.CONTENT_PASTE),
                        data={'sec': "questions", 'act': "topics"},
                        on_click=on_drawer_el_selected),
                ],
            ),
            ft.ListTile(
                title=ft.Text("Темы тренировок"),
                leading=ft.Icon(ft.icons.TOPIC),
                data={'sec': "topics", 'act': "topics"},
                on_click=on_drawer_el_selected),
            ft.ExpansionTile(
                title=ft.Text("Настройки"),
                leading=ft.Icon(ft.icons.SETTINGS),

                controls=[
                    ft.ListTile(
                        title=ft.Text("Изменить пароль"),
                        leading=ft.Icon(ft.icons.PASSWORD),
                        data={'sec': "settings", 'act': "change_password"},
                        on_click=on_drawer_el_selected
                    ),
                    ft.ListTile(
                        title=ft.Text("Состояние системы"),
                        leading=ft.Icon(ft.icons.RESTART_ALT),
                        data={'sec': "settings", 'act': "system_status"},
                        on_click=on_drawer_el_selected
                    ),
                    ft.ListTile(
                        title=ft.Text("О приложении"),
                        leading=ft.Icon(ft.icons.INFO),
                        data={'sec': "settings", 'act': "app_info"},
                        on_click=on_drawer_el_selected
                    ),
                ],
            ),
            ft.Divider(thickness=1),
            ft.ListTile(
                title=ft.Text("Выйти"),
                leading=ft.Icon(ft.icons.LOGOUT, rotate=pi),
                data={'sec': "app", 'act': "exit"},
                on_click=on_drawer_el_selected),

        ],
    )


def show_main_drawer(page: ft.Page):
    page.drawer.open = True
    page.update()
