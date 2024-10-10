from os import getenv

import flet as ft

from utils.image_converter import image_to_base64_2


def get_error_col(page: ft.Page, text: str, disable_scroll: bool, icon_filename: str) -> ft.Column:
    if disable_scroll:
        page.scroll = None

    col = ft.Column(
        controls=[
            ft.Image(
                src_base64=image_to_base64_2(f'{getenv('ROOT_FOLDER')}/flet_apps/assets/images/{icon_filename}'),
                error_content=ft.Icon(ft.icons.ERROR, size=50),
                height=100,
            ),
            ft.Text(
                value=text,
                size=16,
                text_align=ft.TextAlign.CENTER,
            )
        ],
        horizontal_alignment="center",
    )

    return col
