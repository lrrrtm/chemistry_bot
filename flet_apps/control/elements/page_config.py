import flet as ft


def set_page_config(page: ft.Page):
    page.title = "ХимБот"
    page.padding = 0

    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    page.theme_mode = ft.ThemeMode.DARK

    # page.appbar = ft.AppBar(
    #     title=ft.Text(
    #         size=18
    #     ),
    #     bgcolor=ft.colors.SURFACE_VARIANT
    # )

    page.appbar = None
