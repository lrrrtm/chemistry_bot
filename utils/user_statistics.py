from datetime import datetime

from db.crud import (get_user, get_user_works, get_topic_by_id, get_work_questions, get_question_from_pool)
from utils.mark_converter import convert_ege_mark


def get_user_statistics(telegram_id: int):
    result = []

    user_works = get_user_works(telegram_id)
    user_works = [w for w in user_works if w.end_datetime is not None]

    for work in user_works:
        work_stats = {
            'general': {
                'type': work.work_type,
                'work_id': work.id,
                'name': '',
                'time': {
                    'start': work.start_datetime,
                    'end': work.end_datetime,
                }
            },
            'questions': {
                'fully': [],
                'semi': [],
                'zero': [],
            },
            'results': {
                'max_mark': 0,  # макисмально можно было получить
                'recieved_mark': 0,  # для первичных баллов егэ/темы
                'final_mark': 0,  # для вторичных баллов егэ
            }
        }
        if work.work_type == "topic":
            topic = get_topic_by_id(work.topic_id)
            work_stats['general']['name'] = topic.name
        else:
            work_stats['general']['name'] = "КИМ ЕГЭ"

        work_questions = get_work_questions(work.id)
        work_stats['general']['questions_amount'] = len(work_questions)

        work_stats['results']['recieved_mark'] = sum([q.user_mark for q in work_questions])
        work_stats['results']['final_mark'] = work_stats['results']['recieved_mark']

        for question in work_questions:
            original_question = get_question_from_pool(question.id)
            work_stats['results']['max_mark'] += original_question.full_mark
            if question.user_mark == original_question.full_mark:
                work_stats['questions']['fully'].append(question)
            elif 0 < question.user_mark < original_question.full_mark:
                work_stats['questions']['semi'].append(question)
            else:
                work_stats['questions']['zero'].append(question)

        if work.work_type == "ege":
            work_stats['results']['final_mark'] = convert_ege_mark(work_stats['results']['recieved_mark'])
            work_stats['results']['max_mark'] = 100

        result.append(work_stats)
    return result


x = get_user_statistics(409801981)
print(x)
