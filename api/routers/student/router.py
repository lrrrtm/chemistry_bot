from fastapi import APIRouter, HTTPException

from db.crud import get_work_by_token, get_user_by_id, get_work_questions_joined_pool
from utils.user_statistics import get_user_statistics

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/work-stats")
def student_work_stats(token: str):
    work = get_work_by_token(token)
    if not work:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    user = get_user_by_id(work.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    all_stats = get_user_statistics(user.telegram_id)
    work_stats_list = [s for s in all_stats if s["general"]["work_id"] == work.id]
    if not work_stats_list:
        raise HTTPException(status_code=404, detail="Статистика не найдена")

    ws = work_stats_list[-1]
    questions_list = get_work_questions_joined_pool(work.id)

    questions_data = [
        {
            "index": idx + 1,
            "question_id": q.question_id,
            "text": q.text,
            "answer": q.answer,
            "user_answer": q.user_answer,
            "user_mark": q.user_mark if q.user_mark is not None else 0,
            "full_mark": q.full_mark,
            "question_image": bool(q.question_image),
            "answer_image": bool(q.answer_image),
        }
        for idx, q in enumerate(questions_list)
    ]

    return {
        "general": {
            "telegram_id": user.telegram_id,
            "user_name": user.name,
            "name": ws["general"]["name"],
            "start": ws["general"]["time"]["start"].isoformat(),
            "end": ws["general"]["time"]["end"].isoformat(),
            "final_mark": ws["results"]["final_mark"],
            "max_mark": ws["results"]["max_mark"],
            "fully": len(ws["questions"]["fully"]),
            "semi": len(ws["questions"]["semi"]),
            "zero": len(ws["questions"]["zero"]),
        },
        "questions": questions_data,
    }
