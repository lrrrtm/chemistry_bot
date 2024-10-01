def get_ege_tags_list(each_question_limit: int = 1):
    return [{'tag': f"ege_{num}", 'limit': each_question_limit} for num in range(1, 35)]
