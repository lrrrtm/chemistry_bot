import flet as ft


def get_change_password_col(on_change_fields, after_submit_btn_clicked) -> ft.Column:
    """
    Создание column с элементами для смены пароля панели управления
    :param on_change_fields: действие при изменеии значения любого поля
    :param after_submit_btn_clicked: действие при нажатии кнопки сохранения
    :return: 
    """
    col = ft.Column(
        controls=[
            ft.Container(
                content=ft.TextField(
                    password=True,
                    label='Текущий пароль',
                    data="input_current_password",
                    hint_text="*" * 10,
                    on_change=on_change_fields
                ),
                padding=ft.padding.only(top=20)
            ),
            ft.Divider(thickness=1),
            ft.TextField(
                password=True,
                label='Новый пароль',
                data="input_new_password",
                hint_text="*" * 10,
                on_change=on_change_fields
            ),
            ft.TextField(
                password=True,
                label='Подтверждение пароля',
                data="reinput_new_password",
                hint_text="*" * 10,
                on_change=on_change_fields
            ),
            ft.ElevatedButton(
                text="Изменить",
                on_click=after_submit_btn_clicked
                # width=250
            )

        ],
        horizontal_alignment="end",
        width=600
    )

    return col
