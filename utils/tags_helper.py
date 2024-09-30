def get_ege_tag_list(each_question_limit: int = 1):
    return [{'tag': f"ege_{num}", 'limit': each_question_limit} for num in range(1, 35)]
