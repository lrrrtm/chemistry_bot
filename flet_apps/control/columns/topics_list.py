from typing import List

import flet as ft

from db.models import Topic
from flet_apps.control.columns.error import get_error_col


def get_topics_list_col(topics_list: List[Topic], page: ft.Page) -> ft.Column:
    if not topics_list:
        pass
    else:
        return get_error_col(page, "Список тем тренировок пуст", disable_scroll=True, icon_filename="bookshelf.png")