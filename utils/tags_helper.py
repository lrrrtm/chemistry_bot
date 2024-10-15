from typing import List

import random

from db.models import Pool


def get_ege_self_check_tags_list():
    return [f"ege_{n}" for n in range(29, 35)]


def get_ege_tags_list(each_question_limit: int):
    return {f"ege_{num}": each_question_limit for num in range(1, 35)}


def get_random_questions(pool: List[Pool], request_dict: dict) -> dict:
    result = []

    for el in request_dict.keys():

        if len([q.id for q in pool if el in q.tags_list]) < request_dict[el]:
            return {
                'is_ok': False,
                'detail': "more_than_exists",
                'tag': el,
                'requested': request_dict[el],
                'exists': len([q.id for q in pool if el in q.tags_list])
            }

        current_tag_result = []
        current_tag_pool = [q for q in pool if el in q.tags_list and q not in result]
        if len(current_tag_pool) < request_dict[el]:
            return {
                'is_ok': False,
                'detail': "question_already_inserted",
                'tag': el,
                'requested': request_dict[el],
                'exists': len([q.id for q in pool if el in q.tags_list])
            }
        else:
            for __ in range(request_dict[el]):
                q = random.choice(current_tag_pool)
                current_tag_result.append(q.id)
                current_tag_pool.remove(q)

        for q in current_tag_result:
            result.append(q)

    return {
        'is_ok': True,
        'detail': result
    }
