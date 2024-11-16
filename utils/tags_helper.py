from typing import List

import random

from db.crud import get_topic_by_id, get_pool_by_tags
from db.models import Pool


def get_ege_tags_list(each_question_limit: int):
    return {f"ege_{num}": each_question_limit for num in range(1, 35)}


def get_random_questions_for_hard_tags_filter(pool: List[Pool], tags_list: List[str], questions_count: int = 20):
    questions_with_requested_tags = []
    result = []

    for p in pool:
        if all([tag in p.tags_list for tag in tags_list]):
            questions_with_requested_tags.append(p)

    print(len(questions_with_requested_tags))

    if len(questions_with_requested_tags) >= questions_count:
        for _ in range(questions_count):
            q = random.choice(questions_with_requested_tags)
            result.append(q.id)
            questions_with_requested_tags.remove(q)

        return {
            'is_ok': True,
            'detail': result
        }

    else:
        return {
            'is_ok': False,
            'detail': 'more_than_exists'
        }


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


def get_questions_list_for_topic_work(topic_id: int, questions_limit: int = 20) -> dict:
    result_questions_list = []

    topic_data = get_topic_by_id(topic_id)
    topic_tags_list = topic_data.tags_list
    pool_by_topic_tags = get_pool_by_tags(topic_tags_list)
    # print("LEN", len(pool_by_topic_tags))
    # print("TOPIC TAGS", topic_tags_list)

    if len(pool_by_topic_tags) < questions_limit:
        return {
            'is_ok': False,
            'detail': f"more_than_exists ({len(pool_by_topic_tags)} < {questions_limit})",
        }

    elif len(pool_by_topic_tags) == questions_limit:
        return {
            'is_ok': True,
            'detail': pool_by_topic_tags
        }

    else:
        limiter = 100
        while len(result_questions_list) != questions_limit:
            for tag in topic_tags_list:
                filtered_pool = [q for q in pool_by_topic_tags if tag in q.tags_list]
                if filtered_pool:
                    q = random.choice(filtered_pool)
                    result_questions_list.append(q)
                    pool_by_topic_tags.remove(q)

                if len(result_questions_list) == questions_limit:
                    break

            limiter -= 1
            if limiter == 0:
                return {
                    'is_ok': False,
                    'detail': f"while error",
                }

        return {
            'is_ok': True,
            'detail': result_questions_list
        }
