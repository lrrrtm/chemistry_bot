from datetime import datetime
from os import getenv
from typing import List

import openpyxl

from db.models import Topic


def export_topics_list(topics_list: List[Topic]):
    wb = openpyxl.load_workbook(f"{getenv('ROOT_FOLDER')}/data/excel_templates/chembot_topics_list.xlsx")

    sheet_name = "Основной лист"
    sheet = wb[sheet_name]

    data = []
    for topic in topics_list:
        topic_name = topic.name
        for tag in topic.tags_list:
            data.append([topic_name, tag])

    for index, el in enumerate(data):
        sheet.cell(row=index+2, column=1, value=el[0])
        sheet.cell(row=index+2, column=2, value=el[1])

    wb.save(f"{getenv('ROOT_FOLDER')}/data/temp/chembot_topics_list.xlsx")

def import_topics_list(filepath: str):
    wb = openpyxl.load_workbook(filepath)
    sheet_name = "Основной лист"

    result = {}
    errors = []
    try:
        sheet = wb[sheet_name]
    except KeyError:
        return {'is_ok': False, 'comment': f"В файле отсутствует лист \"{sheet_name}\""}

    sheet.cell(row=1, column=3).value = "Статус"

    for row_num in range(2, 102):
        topic_name = sheet.cell(row=row_num, column=1).value
        tag = sheet.cell(row=row_num, column=2).value

        if not all([topic_name is None, tag is None]):
            if topic_name is not None:

                topic_name = str(topic_name).replace("ё", "е")

                if topic_name not in result.keys():
                    result[topic_name] = []

                if tag is not None:

                    tag = str(tag).replace("ё", "е")

                    result[topic_name].append(tag.lower())
                    sheet.cell(row=row_num, column=3).value = "OK"
                else:
                    errors.append({'type': "tag", 'comment': "отсутствие тега", 'pos': {'row': row_num, 'column': 2},
                                   'data': topic_name})
                    sheet.cell(row=row_num, column=3).value = "TAG_ERROR"

            else:
                errors.append(
                    {'type': "name", 'comment': "отсутствие названия темы", 'pos': {'row': row_num, 'column': 1},
                     'data': tag})
                sheet.cell(row=row_num, column=3).value = "NAME_ERROR"
    filename = f"import_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    wb.save(f"{getenv('ROOT_FOLDER')}/data/temp/{filename}")
    return {'is_ok': True, 'comment': "Импорт тем и тегов завершён", 'data': result, 'errors': errors, 'filename': filename}
