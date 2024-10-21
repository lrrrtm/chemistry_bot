from datetime import datetime
from os import getenv
from typing import List

from dotenv import load_dotenv
from openpyxl_image_loader import SheetImageLoader

import openpyxl

from db.models import Topic, Pool

load_dotenv()


def import_pool(filepath: str):
    wb = openpyxl.load_workbook(filepath)
    sheet_name = "Основной лист"
    sheet = wb[sheet_name]

    image_loader = SheetImageLoader(sheet)

    data = []
    errors = []
    try:
        for row_num in range(2, 1002):
            if sheet.cell(row=row_num, column=1).value is not None:
                import_id = f"{len(data) + 1}{datetime.now().strftime("%Y%m%d%H%M%S")}"
                if all(
                        [
                            sheet.cell(row=row_num, column=2).value is not None,
                            sheet.cell(row=row_num, column=3).value is not None,
                            sheet.cell(row=row_num, column=5).value is not None,
                            sheet.cell(row=row_num, column=7).value is not None,
                            sheet.cell(row=row_num, column=8).value is not None,
                            sheet.cell(row=row_num, column=9).value is not None,
                            sheet.cell(row=row_num, column=10).value is not None,
                        ]
                ):
                    question_info = Pool(
                        import_id=import_id,
                        type="ege" if sheet.cell(row=row_num, column=1).value == "КИМ ЕГЭ" else "topic",
                        level=sheet.cell(row=row_num, column=2).value,
                        text=str(sheet.cell(row=row_num, column=3).value),
                        answer=str(sheet.cell(row=row_num, column=5).value),
                        full_mark=sheet.cell(row=row_num, column=7).value,
                        is_rotate=1 if sheet.cell(row=row_num, column=8).value == "Да" else 0,
                        is_selfcheck=1 if sheet.cell(row=row_num, column=9).value == "Да" else 0,
                        tags_list=[tag.lower().replace("ё", "е") for tag in
                                   sheet.cell(row=row_num, column=10).value.split(", ")]
                    )
                    # question_info = {
                    #     'import_id': import_id,
                    #     'type': "ege" if sheet.cell(row=row_num, column=1).value == "КИМ ЕГЭ" else "topic",
                    #     'level': sheet.cell(row=row_num, column=2).value,
                    #     'question_text': str(sheet.cell(row=row_num, column=3).value),
                    #     'answer_text': str(sheet.cell(row=row_num, column=5).value),
                    #     'mark': sheet.cell(row=row_num, column=7).value,
                    #     'is_rotate': bool(sheet.cell(row=row_num, column=8).value),
                    #     'is_selfcheck': bool(sheet.cell(row=row_num, column=9).value),
                    #     'tags_list': [tag.lower().replace("ё", "е") for tag in
                    #                   sheet.cell(row=row_num, column=10).value.split(", ")]
                    #
                    # }
                    try:
                        q_image = image_loader.get(f"D{row_num}")
                        q_image.save(f"{getenv('ROOT_FOLDER')}/data/temp/q_{import_id}.png")
                        question_info.question_image = 1
                        # question_info['question_image'] = 1
                    except ValueError:
                        question_info.question_image = 0

                    try:
                        a_image = image_loader.get(f"F{row_num}")
                        a_image.save(f"{getenv('ROOT_FOLDER')}/data/temp/a_{import_id}.png")
                        question_info.answer_image = 1
                    except ValueError:
                        question_info.answer_image = 0

                    data.append(question_info)
                else:
                    errors.append(import_id)

        return {'is_ok': True, 'data': data, 'comment': "Импорт вопросов завершён", 'errors': errors}
    except Exception as e:
        return {'is_ok': False, 'comment': f"Ошибка при чтении данных таблицы: {str(e)}", 'errors': errors}


def export_pool(data: List[Pool]):
    wb = openpyxl.load_workbook(f"{getenv('ROOT_FOLDER')}/data/excel_templates/chembot_pool_list.xlsx")

    sheet_name = "Основной лист"
    sheet = wb[sheet_name]

    for index, q in enumerate(data):
        sheet.cell(row=index + 2, column=1, value=q.type)
        sheet.cell(row=index + 2, column=2, value=str(q.level))
        sheet.cell(row=index + 2, column=3, value=q.text)
        sheet.cell(row=index + 2, column=5, value=str(q.answer))
        sheet.cell(row=index + 2, column=7, value=str(q.full_mark))
        sheet.cell(row=index + 2, column=8, value="Да" if bool(q.is_rotate) else "Нет")
        sheet.cell(row=index + 2, column=9, value="Да" if bool(q.is_selfcheck) else "Нет")
        sheet.cell(row=index + 2, column=10, value=", ".join(q.tags_list))

    wb.save(f"{getenv('ROOT_FOLDER')}/data/temp/chembot_pool_list.xlsx")


def export_topics_list(data: List[Topic]):
    wb = openpyxl.load_workbook(f"{getenv('ROOT_FOLDER')}/data/excel_templates/chembot_topics_list.xlsx")

    sheet_name = "Основной лист"
    sheet = wb[sheet_name]

    data = []
    for topic in data:
        topic_name = topic.name
        for tag in topic.tags_list:
            data.append([topic_name, tag])

    for index, el in enumerate(data):
        sheet.cell(row=index + 2, column=1, value=el[0])
        sheet.cell(row=index + 2, column=2, value=el[1])

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
                    result[topic_name] = set()

                if tag is not None:

                    tag = str(tag).replace("ё", "е")

                    result[topic_name].add(tag.lower())
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

    for key, value in result.items():
        result[key] = list(value)
    filename = f"topics_import_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    wb.save(f"{getenv('ROOT_FOLDER')}/data/temp/{filename}")
    return {'is_ok': True, 'comment': "Импорт тем и тегов завершён", 'data': result, 'errors': errors,
            'filename': filename}

# print(import_pool(fr"D:\repos\chemistry_bot\test_pool.xlsx"))
