import os
import time
from os import getenv
from urllib.parse import urlparse, parse_qs
import flet as ft

from dotenv import load_dotenv

from flet_apps.control.elements.app_info import get_app_info_col
from flet_apps.control.elements.login_column import get_login_col
from flet_apps.control.elements.main_drawer import get_main_drawer
from flet_apps.control.elements.system_status import get_system_status_col
from flet_apps.control.screens import screens_config
from utils.image_converter import image_to_base64, image_to_base64_2
from utils.services_checker import get_system_status, restart_service

load_dotenv()


def show_snack_bar(snack_bar: ft.SnackBar, text: str, page: ft.Page):
    snack_bar.content.value = text
    snack_bar.open = True
    page.update()


def main(page: ft.Page):
    page.title = "ХимБот"
    page.padding = 0
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    page.theme_mode = ft.ThemeMode.DARK

    page.appbar = ft.AppBar(
        title=ft.Text(
            size=18
        ),
        bgcolor=ft.colors.SURFACE_VARIANT
    )

    text_snack_bar = ft.SnackBar(
        content=ft.Text(
            size=16,
        ),
        show_close_icon=True,
        duration=1500
    )
    page.overlay.append(text_snack_bar)

    def show_main_drawer():
        page.drawer.open = True
        page.update()

    def update_user_input_password(e: ft.ControlEvent):
        page.session.set(
            key='input_password',
            value=e.control.value
        )

    def login_process(e: ft.ControlEvent):
        input_password = page.session.get('input_password')

        if not input_password:
            show_snack_bar(text_snack_bar, "Введите пароль", page)
        elif input_password == os.getenv('PANEL_PASSWORD'):
            change_screen("users")
        else:
            show_snack_bar(text_snack_bar, "Неверный пароль", page)

    def drawer_element_selected(e: ft.ControlEvent):
        data = e.control.data

        page.drawer.open = False
        page.update()

        if data['sec'] == "users":
            if data['act'] == "users":
                change_screen("users")

        elif data['sec'] == "questions":
            if data['act'] == "ege":
                change_screen("ege")
            elif data['act'] == "topics":
                change_screen("topics")

        elif data['sec'] == "settings":
            if data['act'] == "change_password":
                pass
                # change_password()
            elif data['act'] == "system_status":
                change_screen("system_status")
            elif data['act'] == "app_info":
                change_screen("app_info")

        elif data['sec'] == "app":
            if data['act'] == "exit":
                change_screen("login")

    page.drawer = get_main_drawer(
        page=page,
        click_action=drawer_element_selected
    )

    def on_restart_button_click(e: ft.ControlEvent):
        show_snack_bar(text_snack_bar, "Сервис перезагружается", page)
        restart_service(e.control.data)

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
                        on_click=lambda _: show_main_drawer()
                    )
            else:
                page.appbar.leading = ft.IconButton(
                    icon=ft.icons.CIRCLE
                )

        else:
            page.appbar.value = False

        if target == "login":
            page.add(get_login_col(
                login_process=login_process,
                update_user_input_password=update_user_input_password,
            ))

        elif target == "app_info":
            page.add(get_app_info_col())

        elif target == "system_status":
            data = get_system_status()
            page.add(get_system_status_col(data, on_restart_button_click))

        page.update()

    change_screen('system_status')


if __name__ == "__main__":
    ft.app(
        target=main,
        use_color_emoji=True,
        assets_dir=os.path.join(getenv('ROOT_FOLDER'), "flet_apps/assets"),
        view=None,
        port=6001
    )
