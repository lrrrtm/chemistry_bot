import flet as ft

from utils.image_converter import image_to_base64_2


def get_app_info_col() -> ft.Column:
    """
    Создание страницы с информацией о приложении
    :return:
    """
    col = ft.Column(
        controls=[
            ft.Container(
                content=ft.Image(
                    src_base64=image_to_base64_2("flet_apps/assets/icons/loading-animation.png"),
                    height=100,
                ),
                padding=ft.padding.only(top=-30)
            ),
            ft.Text(
                value="ХимБот v1.0",
                size=18,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                value="Панель управления Telegram-ботом для подготовки к ЕГЭ по химии",
                size=16,
                text_align=ft.TextAlign.CENTER,
                width=300
            ),
            ft.Container(
                content=ft.OutlinedButton(
                    text="Разработано @lrrrtm",
                    url="https://github.com/lrrrtm",
                    width=250
                )
            )
        ],
        width=600,
        alignment="center",
        horizontal_alignment="center",
    )

    return col
