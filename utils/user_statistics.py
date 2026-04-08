from typing import List

from db.crud import (
    get_all_pool,
    get_hand_work,
    get_output_mark,
    get_topic_by_id,
    get_user,
    get_user_by_id,
    get_user_works,
    get_user_works_by_user_id,
    get_work_questions,
)
from db.models import WorkQuestion


def remove_none(work_questions_list: List[WorkQuestion]):
    for question in work_questions_list:
        if question.user_mark is None:
            question.user_mark = 0
    return work_questions_list


def _build_user_statistics(user, user_works):
    result = []
    pool = get_all_pool(active=False)
    finished_works = [work for work in user_works if work.end_datetime is not None]

    for work in finished_works:
        work_stats = {
            "general": {
                "user": user,
                "type": work.work_type,
                "work_id": work.id,
                "share_token": work.share_token,
                "name": "",
                "time": {
                    "start": work.start_datetime,
                    "end": work.end_datetime,
                },
            },
            "questions": {
                "fully": [],
                "semi": [],
                "zero": [],
            },
            "results": {
                "max_mark": 0,
                "recieved_mark": 0,
                "final_mark": 0,
            },
        }

        if work.work_type == "topic":
            topic = get_topic_by_id(work.topic_id)
            work_stats["general"]["name"] = topic.name if topic else "Удалённая тема"
        elif work.work_type == "ege":
            work_stats["general"]["name"] = "КИМ ЕГЭ"
        elif work.work_type == "hand_work":
            hand_work = get_hand_work(work.hand_work_id)
            work_stats["general"]["name"] = hand_work.name if hand_work else "Удалённая тренировка"

        work_questions = remove_none(get_work_questions(work.id))
        work_stats["general"]["questions_amount"] = len(work_questions)
        work_stats["results"]["recieved_mark"] = sum(question.user_mark for question in work_questions)
        work_stats["results"]["final_mark"] = work_stats["results"]["recieved_mark"]

        for question in work_questions:
            original_question = next((item for item in pool if item.id == question.question_id), None)
            if original_question is None:
                work_stats["questions"]["zero"].append(question)
                continue

            work_stats["results"]["max_mark"] += original_question.full_mark
            if question.user_mark == original_question.full_mark:
                work_stats["questions"]["fully"].append(question)
            elif 0 < question.user_mark < original_question.full_mark:
                work_stats["questions"]["semi"].append(question)
            else:
                work_stats["questions"]["zero"].append(question)

        if work.work_type == "ege":
            work_stats["results"]["final_mark"] = get_output_mark(work_stats["results"]["recieved_mark"])
            work_stats["results"]["max_mark"] = 100

        result.append(work_stats)

    return result


def get_user_statistics(telegram_id: int):
    user = get_user(telegram_id)
    user_works = get_user_works(telegram_id)
    return _build_user_statistics(user, user_works)


def get_user_statistics_by_user_id(user_id: int):
    user = get_user_by_id(user_id)
    user_works = get_user_works_by_user_id(user_id)
    return _build_user_statistics(user, user_works)
