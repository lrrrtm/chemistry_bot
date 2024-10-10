import flet as ft


def get_system_status_col(data: list, on_restart_button_click) -> ft.Column:
    col = ft.Column(
        horizontal_alignment="center",
    )

    for el in data:
        col.controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.ListTile(
                                            leading=ft.Icon(el['flet_icon']),
                                            title=ft.Text(
                                                value=el['name']
                                            ),
                                            subtitle=ft.Text(
                                                value=el['status']
                                            ),
                                            width=280
                                        ),
                                        padding=ft.padding.only(left=-15)
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.RESTART_ALT,
                                        on_click=on_restart_button_click,
                                        data=el
                                    )
                                ],
                                alignment="center"
                            )
                        ]
                    ),
                    padding=10
                ),
                width=600
            )

        )

    return col
