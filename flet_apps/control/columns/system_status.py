import flet as ft


def get_system_status_col(data: list, after_reboot_btn_clicked) -> ft.Column:
    """
    Создание column для страницы с состоянием системы
    :param data: List(Dict) с информацией о каждом сервисе
    :param after_reboot_btn_clicked: действие при нажатии на кнопку перезагрузки сервиса
    :return:
    """
    col = ft.Column(
        horizontal_alignment="center",
    )

    for el in data:
        col.controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.ListTile(
                                    leading=ft.Icon(el['flet_icon']),
                                    title=ft.Text(
                                        value=el['name']
                                    ),
                                    subtitle=ft.Text(
                                        value=el['status']
                                    )
                                ),
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.IconButton(
                                    icon=ft.icons.RESTART_ALT,
                                    on_click=after_reboot_btn_clicked,
                                    data=el
                                ),
                                padding=ft.padding.only(right=10)
                            )
                        ],
                        alignment="start"
                    ),
                    padding=10
                ),
                width=600
            )

        )

    return col
