import sys
import os
from typing import List

from utils.image_converter import image_to_base64

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from os import getenv
from urllib.parse import urlparse, parse_qs
import flet as ft
from utils.user_statistics import get_user_statistics
from db.crud import get_work_by_url_data, get_work_questions_joined_pool
from db.models import Work, WorkQuestion
from dotenv import load_dotenv

load_dotenv()


def get_info_column(caption: str, icon_filename: str, progress_bar_visible: bool = False) -> ft.Column:
    error_column = ft.Column(
        controls=[
            ft.Image(
                src=f"/images/{icon_filename}",
                error_content=ft.Icon(ft.icons.ERROR, size=50),
                width=150
            ),
            ft.Text(caption, size=16,
                    text_align=ft.TextAlign.LEFT),
            ft.ProgressBar(
                visible=progress_bar_visible,
                width=100
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        width=300
    )

    return error_column


def get_general_info_card(stats: dict, page: ft.Page):
    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Общий обзор", size=20),
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.icons.SCHOOL, color=ft.colors.AMBER),
                            title=ft.Text(stats['general']['name']),
                            subtitle=ft.Text("название работы"),
                        ),
                        padding=ft.padding.only(left=-15, bottom=-25)
                    ),
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.icons.ACCESS_TIME, color=ft.colors.CYAN),
                            title=ft.Text(f"{stats['general']['time']['end'] - stats['general']['time']['start']}"),
                            subtitle=ft.Text("затраченное время"),
                        ),
                        padding=ft.padding.only(left=-15, bottom=-25)
                    ),
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.icons.INSERT_CHART, color=ft.colors.GREEN),
                            title=ft.Text(f"{stats['results']['final_mark']}/{stats['results']['max_mark']}"),
                            subtitle=ft.Text("результат"),
                        ),
                        padding=ft.padding.only(left=-15, bottom=-10)
                    ),
                    # ft.Container(
                    #     content=ft.ListTile(
                    #         leading=ft.Icon(ft.icons.FORMAT_LIST_NUMBERED),
                    #         title=ft.Text(
                    #             f"{len(stats['questions']['fully'])} | {len(stats['questions']['semi'])} | {len(stats['questions']['zero'])}"),
                    #         subtitle=ft.Text("полностью | частично | не решено"),
                    #     ),
                    #     padding=ft.padding.only(left=-15, bottom=0)
                    # )
                    ft.Divider(thickness=1),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("полностью"),
                                    ft.Text(f"{len(stats['questions']['fully'])}", size=16),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("частично"),
                                    ft.Text(f"{len(stats['questions']['semi'])}", size=16),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("не решено"),
                                    ft.Text(f"{len(stats['questions']['zero'])}", size=16),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        expand=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                ],

            ),
            padding=15
        )
    )

    return card


def get_questions_info_card(questions_list: List[WorkQuestion], page: ft.Page) -> ft.Card:
    card_controls = [ft.Container(ft.Text("Подробности", size=20), padding=ft.padding.only(left=10, top=10))]

    for index, question in enumerate(questions_list):

        if question.full_mark == question.user_mark:
            card_color = ft.colors.GREEN
        elif 0 < question.user_mark < question.full_mark:
            card_color = ft.colors.AMBER
        else:
            card_color = ft.colors.RED



        card_controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            # ft.Container(
                            #     ft.ListTile(
                            #         leading=ft.Icon(ft.icons.CIRCLE, color=card_color),
                            #         title=ft.Text(f"№{index + 1}"),
                            #     ),
                            #     padding=ft.padding.only(top=-25)
                            # ),
                            ft.Container(ft.Row([ft.Icon(ft.icons.CIRCLE, color=card_color), ft.Text(f"№ {index + 1}", size=18)]), padding=ft.padding.only(left=10, top=10)),
                            ft.Image(
                                src_base64=image_to_base64(
                                    question.question_id) if bool(question.question_image) else None,
                                error_content=ft.Text("Не удалось загрузить изображение с заданием", size=14),
                                # border_radius=10,
                                visible=bool(question.question_image)
                            ),
                            ft.ListTile(
                                title=ft.Text(f"{question.text}"),
                                subtitle=ft.Column(
                                    [
                                        ft.Divider(thickness=1),
                                        ft.Text(
                                            f"Баллы: {question.user_mark} из {question.full_mark}\nВерный ответ: {question.answer}\nТвой ответ: {question.user_answer}")
                                    ]
                                ),
                            )
                        ]
                    ),
                    # padding=ft.padding.only(left=-5, bottom=10, top=10, right=10)
                ),
                surface_tint_color=card_color,
            )
        )

    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=card_controls

            ),
            padding=5
        )
    )

    return card


def main(page: ft.Page):
    page.title = "ХимБот"
    page.padding = 0
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    page.theme_mode = ft.ThemeMode.DARK

    url_params = {key: int(value[0]) for key, value in parse_qs(urlparse(page.route).query).items()}

    if all(key in url_params for key in ['uuid', 'tid', 'work']) and get_work_by_url_data(url_params['uuid'],
                                                                                          url_params['tid'],
                                                                                          url_params['work']):
        col = get_info_column("Загружаем информацию", progress_bar_visible=True, icon_filename='loading.png')
        page.add(col)

        page.scroll = ft.ScrollMode.AUTO

        all_stats = get_user_statistics(url_params['tid'])
        work_stats = [s for s in all_stats if s['general']['work_id'] == url_params['work']][-1]
        questions_list = get_work_questions_joined_pool(int(url_params['work']))

        main_col = ft.Column(
            controls=[
                get_general_info_card(work_stats, page),
                get_questions_info_card(questions_list, page)
            ],
            width=700
        )

        page.controls = [main_col]
        page.update()
    else:
        col = get_info_column("Некорректная ссылка, попробуй ещё раз или напиши в поддержку через команду /feedback",
                              icon_filename='error.png')
        page.add(col)


if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir=os.path.join(getenv('ROOT_FOLDER'), "flet_apps/assets"),
        view=None,
        port=6002
    )
