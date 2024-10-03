from db.models import Pool


def count_matches(correct_answer, user_answer):
    matches = 0
    for i in range(min(len(correct_answer), len(user_answer))):
        if correct_answer[i] == user_answer[i]:
            matches += 1
    return matches


def check_answer(question_data: Pool, user_answer: str) -> int:
    if question_data.type == "ege":
        if question_data.full_mark == 2:
            matches = count_matches(question_data.answer, user_answer)
            if matches == len(question_data.answer):
                return 2
            elif matches == len(question_data.answer) - 1:
                return 1
            else:
                return 0

        elif question_data.full_mark == 1:
            if question_data.is_rotate:
                if question_data.answer in [user_answer, user_answer[::-1]]:
                    return 1
            else:
                if question_data.answer in user_answer:
                    return 1
            return 0


    elif question_data.type == "topic":
        if question_data.answer == user_answer:
            return question_data.full_mark
        else:
            return 0
