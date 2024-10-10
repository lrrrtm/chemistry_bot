import time
from math import pi
from os import getenv, path
import flet as ft

from dotenv import load_dotenv

from db.crud import get_all_users, get_all_topics

from columns.app_info import get_app_info_col
from columns.change_password import get_change_password_col
from columns.login import get_login_col
from columns.system_status import get_system_status_col
from columns.user_info import get_user_info_col
from columns.users_col import get_users_col

# from elements.main_drawer import get_main_drawer, show_main_drawer
from elements.overlays import add_elements_to_overlay, text_snack_bar, switch_progress_bar
from elements.page_config import set_page_config
from elements.snack_bar import show_snack_bar
from flet_apps.control.columns.error import get_error_col
from flet_apps.control.columns.topics_list import get_topics_list_col

from screens import screens_config

from utils.env_updater import update_env_variable
from utils.services_checker import get_system_status, restart_service
from utils.user_statistics import get_user_statistics

import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG)


def main(page: ft.Page):
    set_page_config(page)
    add_elements_to_overlay(page)

    def show_content_after_loading(content):
        switch_progress_bar(False, page)
        page.add(content)

    def update_user_input_password(e: ft.ControlEvent):
        page.session.set(
            key='input_password',
            value=e.control.value
        )

    def login_process(e: ft.ControlEvent):
        input_password = page.session.get('input_password')

        if not input_password:
            show_snack_bar(text_snack_bar, "Введите пароль", page)
        elif input_password == getenv('PANEL_PASSWORD'):
            change_screen("system_status")
        else:
            show_snack_bar(text_snack_bar, "Неверный пароль", page)

    def drawer_element_selected(e: ft.ControlEvent):
        data = e.control.data

        page.drawer.open = False
        page.update()

        time.sleep(0.3)

        if data['sec'] == "users":
            if data['act'] == "users":
                change_screen("users")

        elif data['sec'] == "questions":
            if data['act'] == "ege":
                change_screen("ege_questions")
            elif data['act'] == "topics":
                change_screen("topics_questions")

        elif data['sec'] == 'topics':
            if data['act'] == 'topics':
                change_screen("topics_list")

        elif data['sec'] == "settings":
            if data['act'] == "change_password":
                change_screen("change_password")
            elif data['act'] == "system_status":
                change_screen("system_status")
            elif data['act'] == "app_info":
                change_screen("app_info")

        elif data['sec'] == "app":
            if data['act'] == "exit":
                change_screen("login")

    def show_main_drawer(page: ft.Page):
        page.drawer.open = True
        page.update()

    page.drawer = ft.NavigationDrawer(
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
                on_click=drawer_element_selected),

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
                        on_click=drawer_element_selected),
                    ft.ListTile(
                        title=ft.Text("Тренировки"),
                        # subtitle=ft.Text("Перевод ребёнка в другую группу"),
                        leading=ft.Icon(ft.icons.CONTENT_PASTE),
                        data={'sec': "questions", 'act': "topics"},
                        on_click=drawer_element_selected),
                ],
            ),
            ft.ListTile(
                title=ft.Text("Темы тренировок"),
                leading=ft.Icon(ft.icons.TOPIC),
                data={'sec': "topics", 'act': "topics"},
                on_click=drawer_element_selected),
            ft.ExpansionTile(
                title=ft.Text("Настройки"),
                leading=ft.Icon(ft.icons.SETTINGS),

                controls=[
                    ft.ListTile(
                        title=ft.Text("Изменить пароль"),
                        leading=ft.Icon(ft.icons.PASSWORD),
                        data={'sec': "settings", 'act': "change_password"},
                        on_click=drawer_element_selected
                    ),
                    ft.ListTile(
                        title=ft.Text("Состояние системы"),
                        leading=ft.Icon(ft.icons.RESTART_ALT),
                        data={'sec': "settings", 'act': "system_status"},
                        on_click=drawer_element_selected
                    ),
                    ft.ListTile(
                        title=ft.Text("О приложении"),
                        leading=ft.Icon(ft.icons.INFO),
                        data={'sec': "settings", 'act': "app_info"},
                        on_click=drawer_element_selected
                    ),
                ],
            ),
            ft.Divider(thickness=1),
            ft.ListTile(
                title=ft.Text("Выйти"),
                leading=ft.Icon(ft.icons.LOGOUT, rotate=pi),
                data={'sec': "app", 'act': "exit"},
                on_click=drawer_element_selected),

        ],
    )

    def on_restart_button_clicked(e: ft.ControlEvent):
        show_snack_bar(text_snack_bar, "Сервис перезагружается", page)
        restart_service(e.control.data)

    def update_change_password_fields(e: ft.ControlEvent):
        data = page.session.get('change_password')
        data[e.control.data] = e.control.value
        page.session.set('change_password', data)

    def update_password(e: ft.ControlEvent):
        data = page.session.get('change_password')

        if all([el for el in data.values()]):
            if data['input_current_password'] == getenv('PANEL_PASSWORD'):

                if data['input_new_password'] == data['reinput_new_password']:
                    update_env_variable(
                        env_file_path=f"{getenv('ROOT_FOLDER')}/.env",
                        var_name="PANEL_PASSWORD",
                        new_value=data['input_new_password']
                    )
                    show_snack_bar(text_snack_bar, "Пароль изменён!", page)
                    # todo: перезагрузка .service

                else:
                    show_snack_bar(text_snack_bar, "Новый пароль не совпадает", page)

            else:
                show_snack_bar(text_snack_bar, "Неверный текущий пароль", page)
        else:
            show_snack_bar(text_snack_bar, "Заполните все поля", page)

    def show_user_info(e: ft.ControlEvent):
        change_screen("user_info")
        switch_progress_bar(True, page)

        user_stats = get_user_statistics(e.control.data.telegram_id)
        show_content_after_loading(get_user_info_col(e.control.data, user_stats, page))

    def change_screen(target: str):
        screen = screens_config[target]
        page.controls.clear()

        page.scroll = screen['scroll']

        if screen['appbar']['visible']:
            page.appbar.title.value = screen['appbar']['title']

            leading = screen['appbar']['leading']
            if leading['visible']:

                if leading['action'] == "change_screen":
                    page.appbar.leading = ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda _: change_screen(leading['action_context'])
                    )
                elif leading['action'] == "drawer":
                    page.appbar.leading = ft.IconButton(
                        icon=ft.icons.MENU,
                        on_click=lambda _: show_main_drawer(page)
                    )
            else:
                page.appbar.leading = ft.IconButton(
                    icon=ft.icons.CIRCLE
                )

        else:
            page.appbar.visible = False

        if target == "login":
            page.add(get_login_col(
                after_login_btn_clicked=login_process,
                on_password_field_update=update_user_input_password,
            ))

        elif target == "app_info":
            page.add(get_app_info_col())

        elif target == "system_status":
            switch_progress_bar(True, page)

            data = get_system_status()
            show_content_after_loading(get_system_status_col(data, on_restart_button_clicked))

        elif target == "topics_list":
            switch_progress_bar(True, page)

            data = get_all_topics()
            show_content_after_loading(get_topics_list_col(data, page))

        elif target == "change_password":
            page.session.set(
                key='change_password',
                value={
                    'input_current_password': "",
                    'input_new_password': "",
                    'reinput_new_password': "",
                }
            )
            page.add(get_change_password_col(
                on_change_fields=update_change_password_fields,
                after_submit_btn_clicked=update_password
            ))

        elif target == "users":
            switch_progress_bar(True, page)

            users_list = get_all_users()
            if users_list:
                show_content_after_loading(get_users_col(users_list, show_user_info))
            else:
                show_content_after_loading(
                    get_error_col(page, "Список учеников пуст", disable_scroll=True, icon_filename='student.png'))

        page.update()

    change_screen('system_status')


if __name__ == "__main__":
    ft.app(
        target=main,
        use_color_emoji=True,
        assets_dir=path.join(getenv('ROOT_FOLDER'), "flet_apps/assets"),
        view=None,
        port=6001
    )
