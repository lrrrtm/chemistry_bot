from datetime import datetime
from typing import List

from db.crud import (get_user, get_user_works, get_topic_by_id, get_work_questions, get_question_from_pool,
                     get_output_mark, get_hand_work)
from db.models import WorkQuestion
from utils.mark_converter import convert_ege_mark

def remove_none(work_questions_list: List[WorkQuestion]):
    for q in work_questions_list:
        if q.user_mark is None:
            q.user_mark = 0

    return work_questions_list

def get_user_statistics(telegram_id: int):
    # todo: разнести статистику по всем тренировкам и статистику по одной тренировке
    # todo: убрать костыль, связанный с None в user_answer
    result = []

    user = get_user(telegram_id)
    user_works = get_user_works(telegram_id)
    user_works = [w for w in user_works if w.end_datetime is not None]

    for work in user_works:
        work_stats = {
            'general': {
                'user': user,
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
        elif work.work_type == "ege":
            work_stats['general']['name'] = "КИМ ЕГЭ"
        elif work.work_type == "hand_work":
            work_stats['general']['name'] = get_hand_work(work.hand_work_id).name

        work_questions = get_work_questions(work.id)
        work_questions = remove_none(work_questions)
        work_stats['general']['questions_amount'] = len(work_questions)

        work_stats['results']['recieved_mark'] = sum([q.user_mark for q in work_questions])
        work_stats['results']['final_mark'] = work_stats['results']['recieved_mark']

        for question in work_questions:
            original_question = get_question_from_pool(question.question_id)
            work_stats['results']['max_mark'] += original_question.full_mark
            if question.user_mark == original_question.full_mark:
                work_stats['questions']['fully'].append(question)
            elif 0 < question.user_mark < original_question.full_mark:
                work_stats['questions']['semi'].append(question)
            else:
                work_stats['questions']['zero'].append(question)

        if work.work_type == "ege":
            work_stats['results']['final_mark'] = get_output_mark(work_stats['results']['recieved_mark'])
            work_stats['results']['max_mark'] = 100

        result.append(work_stats)
    return result
