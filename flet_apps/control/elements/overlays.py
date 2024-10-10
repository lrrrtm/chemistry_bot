import time

import flet as ft

global_progress_bar = ft.ProgressBar(visible=False)

text_snack_bar = ft.SnackBar(
    content=ft.Text(
        size=16,
    ),
    show_close_icon=True,
    duration=1500
)


def add_elements_to_overlay(page: ft.Page):
    """
    Добавляет элементы в page.overlay
    :param page:
    :return:
    """
    # page.overlay.append(global_progress_bar)
    page.overlay.append(text_snack_bar)


def switch_progress_bar(value: bool, page: ft.Page):
    if value:
        page.controls.clear()
    global_progress_bar.visible = value
    page.update()

    if value:
        time.sleep(1)
