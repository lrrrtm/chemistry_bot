from os import getenv
from urllib.parse import urlparse, parse_qs
import flet as ft

from db.crud import get_work_by_url_data
from dotenv import load_dotenv

load_dotenv()


def main(page: ft.Page):
    page.title = "ХимБот"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    # page.route = "/stats?uuid=8&tid=409801981&work=10"
    url_params = {key: int(value[0]) for key, value in parse_qs(urlparse(page.route).query).items()}

    if all(key in url_params for key in ['uuid', 'tid', 'work']) and get_work_by_url_data(url_params['uuid'], url_params['tid'], url_params['work']):
        page.scroll = ft.ScrollMode.AUTO

        work = get_work_by_url_data(url_params['uuid'], url_params['tid'], url_params['work'])
        col = ft.Column(
            [
                ft.Card(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Общая информация", size=20),
                                ft.Container(
                                    ft.ListTile(
                                        title=ft.Text("КИМ ЕГЭ #10"),
                                        subtitle=ft.Text("Выполненная работа")
                                    ),
                                    padding=ft.padding.only(bottom=-25)
                                ),
                                ft.Container(
                                    ft.ListTile(
                                        title=ft.Text("00:45:38"),
                                        subtitle=ft.Text("Затрачено времени")
                                    ),
                                    padding=ft.padding.only(bottom=-25)
                                ),
                                ft.Container(
                                    ft.ListTile(
                                        title=ft.Text("97/100"),
                                        subtitle=ft.Text("Полученные баллы")
                                    ),
                                    padding=ft.padding.only(bottom=0)
                                ),
                            ]
                        ),
                        padding=10
                    ),
                    width=600
                ),
                ft.Card(
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Подробности", size=20),
                                ft.Container(
                                    ft.ListTile(
                                        title=ft.Text("КИМ ЕГЭ #10"),
                                        subtitle=ft.Text("Выполненная работа")
                                    ),
                                    padding=ft.padding.only(bottom=-25)
                                ),
                                ft.Container(
                                    ft.ListTile(
                                        title=ft.Text("00:45:38"),
                                        subtitle=ft.Text("Затрачено времени")
                                    ),
                                    padding=ft.padding.only(bottom=-25)
                                ),
                                ft.Container(
                                    ft.ListTile(
                                        title=ft.Text("97/100"),
                                        subtitle=ft.Text("Полученные баллы")
                                    ),
                                    padding=ft.padding.only(bottom=0)
                                ),
                            ]
                        ),
                        padding=10
                    ),
                    width=600
                ),
            ]
        )
        page.add(
            col
            # ft.Column(
            #     controls=[
            #         ft.Image(
            #             src="/images/loading.png",
            #             width=150
            #         ),
            #         ft.Text("Загружаем твою статистику", size=16,
            #                 text_align=ft.TextAlign.CENTER),
            #         ft.ProgressRing(scale=0.5)
            #     ],
            #     alignment=ft.MainAxisAlignment.CENTER,
            #     horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            #     width=300
            # )
        )
    else:
        page.add(
            ft.Column(
                controls=[
                    ft.Image(
                        src="/images/error.png",
                        width=150
                    ),
                    ft.Text("Некорректная ссылка, попробуй ещё раз или напиши в поддержку", size=16, text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=300
            )
        )


if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir=f"{getenv('ROOT_FOLDER')}/repos/chemistry_bot/flet_apps/assets",
        view=None,
        port=6002
    )
