import flet as ft

from utils.image_converter import image_to_base64_2


def get_login_col(after_login_btn_clicked, on_password_field_update) -> ft.Column:
    """
    Создание column с элементами авторизации
    :param after_login_btn_clicked: действие при нажатии на кнопку входа
    :param on_password_field_update: действие при изменении поля с паролем
    :return: 
    """
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
                on_change=on_password_field_update,
                on_submit=after_login_btn_clicked
            ),
            ft.FilledButton(
                text="Войти",
                width=300,
                on_click=after_login_btn_clicked
            )
        ],
        width=300,
        horizontal_alignment="center",
    )

    return col
