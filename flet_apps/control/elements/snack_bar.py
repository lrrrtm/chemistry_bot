import flet as ft


def show_snack_bar(snack_bar: ft.SnackBar, text: str, page: ft.Page):
    snack_bar.content.value = text
    snack_bar.open = True
    page.update()
