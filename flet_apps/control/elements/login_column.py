import flet as ft

from utils.image_converter import image_to_base64_2


def get_login_col(login_process, update_user_input_password) -> ft.Column:
    col = ft.Column(
        controls=[
            ft.Image(
                src_base64=image_to_base64_2("flet_apps/assets/icons/loading-animation.png"),
                height=100
            ),
            ft.Text(
                value="ХимБот | Панель управления",
                size=16,
                text_align=ft.TextAlign.CENTER
            ),
            ft.TextField(
                password=True,
                label="Пароль",
                hint_text="*" * 10,
                text_align=ft.TextAlign.CENTER,
                on_change=update_user_input_password,
                on_submit=login_process
            ),
            ft.FilledButton(
                text="Войти",
                width=300,
                on_click=login_process
            )
        ],
        width=300,
        horizontal_alignment="center",
    )

    return col
