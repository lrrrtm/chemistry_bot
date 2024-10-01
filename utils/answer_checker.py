from db.models import Pool


def count_matches(correct_answer, user_answer):
    matches = 0
    for i in range(min(len(correct_answer), len(user_answer))):
        if correct_answer[i] == user_answer[i]:
            matches += 1
    return matches


def check_answer(qusetion_data: Pool, user_answer: str) -> int:
    if qusetion_data.type == "ege":
        matches = count_matches(qusetion_data.answer, user_answer)

        if matches == 4:
            return 2
        elif matches == 3:
            return 1
        else:
            return 0


    elif qusetion_data.type == "topic":
        if qusetion_data.answer == user_answer:
            return qusetion_data.full_mark
        else:
            return 0
