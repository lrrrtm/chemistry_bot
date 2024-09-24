from db.crud import (get_user, get_user_works, get_topic, get_work_questions, get_question_from_pool)


def convert_ege_mark(input_mark: int):
    # todo: реализовать перевод баллов через бд
    return input_mark * 10
