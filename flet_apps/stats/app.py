import sys
import os
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from os import getenv
from urllib.parse import urlparse, parse_qs
import flet as ft
from utils.user_statistics import get_user_statistics
from db.crud import get_work_by_url_data, get_work_questions_joined_pool
from db.models import Work, WorkQuestion
from dotenv import load_dotenv

load_dotenv()


def get_error_column(caption: str) -> ft.Column:
    error_column = ft.Column(
        controls=[
            ft.Image(
                src="/images/error.png",
                error_content=ft.Icon(ft.icons.ERROR, size=50),
                width=150
            ),
            ft.Text(caption, size=16,
                    text_align=ft.TextAlign.LEFT),
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
                        padding=ft.padding.only(left=-15, bottom=-25)
                    ),
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.icons.FORMAT_LIST_NUMBERED),
                            title=ft.Text(
                                f"{len(stats['questions']['fully'])} | {len(stats['questions']['semi'])} | {len(stats['questions']['zero'])}"),
                            subtitle=ft.Text("полностью | частично | не решено"),
                        ),
                        padding=ft.padding.only(left=-15, bottom=0)
                    )
                ],

            ),
            padding=15
        )
    )

    return card


def get_questions_info_card(questions_list: List[WorkQuestion], page: ft.Page) -> ft.Card:
    card_controls = [ft.Text("Подробности", size=20)]

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
                    content=ft.ListTile(
                        title=ft.Text(f"{index + 1}. {question.text}"),
                        subtitle=ft.Text(f"Верный ответ: {question.answer}\nТвой ответ: {question.user_answer}"),
                    ),
                    padding=ft.padding.only(left=-5, bottom=10, top=10, right=10)
                ),
                surface_tint_color=card_color,
            )
        )

    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                controls=card_controls

            ),
            padding=15
        )
    )

    return card


def main(page: ft.Page):
    page.title = "ХимБот"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"

    # page.route = "/stats?uuid=8&tid=409801981&work=10"
    url_params = {key: int(value[0]) for key, value in parse_qs(urlparse(page.route).query).items()}

    if all(key in url_params for key in ['uuid', 'tid', 'work']) and get_work_by_url_data(url_params['uuid'],
                                                                                          url_params['tid'],
                                                                                          url_params['work']):
        page.scroll = ft.ScrollMode.AUTO

        all_stats = get_user_statistics(url_params['tid'])
        work_stats = [s for s in all_stats if s['general']['work_id'] == url_params['work']][-1]
        questions_list = get_work_questions_joined_pool(int(url_params['work']))

        page.add(get_general_info_card(work_stats, page))
        page.add(get_questions_info_card(questions_list, page))
    else:
        col = get_error_column("Некорректная ссылка, попробуй ещё раз или напиши в поддержку через команду /feedback")
        page.add(col)


if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir=f"{getenv('ROOT_FOLDER')}/repos/chemistry_bot/flet_apps/assets",
        view=None,
        port=6002
    )
