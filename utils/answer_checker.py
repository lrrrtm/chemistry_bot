from db.models import Pool


def check_answer(qusetion_data: Pool, user_answer: str) -> int:
    if qusetion_data.type == "ege":
        pass

    elif qusetion_data.type == "topic":
        if qusetion_data.answer == user_answer:
            return qusetion_data.full_mark
        else:
            return 0
