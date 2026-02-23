import os
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from api.config import ROOT_FOLDER
from api.dependencies import require_auth
from api.routers.pool.schemas import NewQuestion, QuestionUpdate
from db.crud import (
    deactivate_question,
    get_all_pool,
    get_question_from_pool,
    insert_pool_data,
    insert_question_into_pool,
    switch_image_flag,
    update_question,
)
from db.models import Pool
from utils.clearing import clear_folder
from utils.excel import import_pool
from utils.move_file import move_image

router = APIRouter(prefix="/api/admin/pool", tags=["pool"])


@router.get("")
def list_pool(_: str = Depends(require_auth)):
    pool = get_all_pool(active=True)
    return [{"id": q.id, "text": q.text, "tags_list": q.tags_list} for q in pool]


@router.get("/template")
def get_pool_template(_: str = Depends(require_auth)):
    filepath = os.path.join(
        ROOT_FOLDER, "data", "excel_templates", "chembot_pool_list.xlsx"
    )
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="chembot_pool_list.xlsx",
    )


@router.post("/import")
def import_pool_excel(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    _: str = Depends(require_auth),
):
    filepath = os.path.join(
        ROOT_FOLDER,
        "data",
        "temp",
        f"pool_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx",
    )
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(file.file.read())

    import_data = import_pool(filepath)

    if not import_data["is_ok"]:
        clear_folder(os.path.join(ROOT_FOLDER, "data", "temp"))
        raise HTTPException(status_code=400, detail=import_data["comment"])

    if import_data["errors"]:
        clear_folder(os.path.join(ROOT_FOLDER, "data", "temp"))
        error_rows = " ".join(str(r) for r in import_data["errors"])
        raise HTTPException(
            status_code=400,
            detail=f"Ошибки в строках: {error_rows}. Исправьте и повторите загрузку.",
        )

    pool = insert_pool_data(import_data["data"])

    for el in pool:
        if bool(el.question_image):
            src = os.path.join(ROOT_FOLDER, "data", "temp", f"q_{el.import_id}.png")
            if os.path.exists(src):
                move_image(
                    src,
                    os.path.join(ROOT_FOLDER, "data", "images", "questions", f"{el.id}.png"),
                )
        if bool(el.answer_image):
            src = os.path.join(ROOT_FOLDER, "data", "temp", f"a_{el.import_id}.png")
            if os.path.exists(src):
                move_image(
                    src,
                    os.path.join(ROOT_FOLDER, "data", "images", "answers", f"{el.id}.png"),
                )

    background_tasks.add_task(clear_folder, os.path.join(ROOT_FOLDER, "data", "temp"))
    return {
        "ok": True,
        "imported_count": len(import_data["data"]),
        "message": f"Вопросы успешно импортированы ({len(import_data['data'])})",
    }


@router.get("/{question_id}")
def get_pool_question(question_id: int, _: str = Depends(require_auth)):
    q = get_question_from_pool(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    return {
        "id": q.id,
        "text": q.text,
        "answer": q.answer,
        "level": q.level,
        "full_mark": q.full_mark,
        "tags_list": q.tags_list,
        "is_rotate": q.is_rotate,
        "is_selfcheck": q.is_selfcheck,
        "question_image": bool(q.question_image),
        "answer_image": bool(q.answer_image),
        "type": q.type,
        "is_active": q.is_active,
    }


@router.put("/{question_id}")
def update_pool_question(
    question_id: int, data: QuestionUpdate, _: str = Depends(require_auth)
):
    q = get_question_from_pool(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    q.text = data.text
    q.answer = data.answer
    q.level = data.level
    q.full_mark = data.full_mark
    q.tags_list = data.tags_list
    q.is_rotate = data.is_rotate
    q.is_selfcheck = data.is_selfcheck
    update_question(q)
    return {"ok": True}


@router.delete("/{question_id}")
def delete_pool_question(question_id: int, _: str = Depends(require_auth)):
    deactivate_question(question_id)
    return {"ok": True}


@router.post("")
def add_question(data: NewQuestion, _: str = Depends(require_auth)):
    q = insert_question_into_pool(
        Pool(
            text=data.text,
            answer=data.answer,
            type=data.type,
            level=data.level,
            full_mark=data.full_mark,
            tags_list=data.tags_list,
            question_image=0,
            answer_image=0,
            is_selfcheck=int(data.is_selfcheck),
            is_rotate=int(data.is_rotate),
            created_at=datetime.now(),
            is_active=1,
        )
    )
    return {"id": q.id, "ok": True}


@router.post("/{question_id}/question-image")
def upload_question_image(
    question_id: int,
    file: UploadFile = File(...),
    _: str = Depends(require_auth),
):
    dest = os.path.join(ROOT_FOLDER, "data", "images", "questions", f"{question_id}.png")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(file.file.read())
    switch_image_flag(1, "question", question_id)
    return {"ok": True}


@router.delete("/{question_id}/question-image")
def remove_question_image(question_id: int, _: str = Depends(require_auth)):
    old = os.path.join(ROOT_FOLDER, "data", "images", "questions", f"{question_id}.png")
    if os.path.exists(old):
        new_path = os.path.join(
            ROOT_FOLDER,
            "data",
            "images",
            "questions",
            f"removed_{datetime.now().timestamp()}_{question_id}.png",
        )
        os.rename(old, new_path)
    switch_image_flag(0, "question", question_id)
    return {"ok": True}


@router.post("/{question_id}/answer-image")
def upload_answer_image(
    question_id: int,
    file: UploadFile = File(...),
    _: str = Depends(require_auth),
):
    dest = os.path.join(ROOT_FOLDER, "data", "images", "answers", f"{question_id}.png")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(file.file.read())
    switch_image_flag(1, "answer", question_id)
    return {"ok": True}


@router.delete("/{question_id}/answer-image")
def remove_answer_image(question_id: int, _: str = Depends(require_auth)):
    old = os.path.join(ROOT_FOLDER, "data", "images", "answers", f"{question_id}.png")
    if os.path.exists(old):
        new_path = os.path.join(
            ROOT_FOLDER,
            "data",
            "images",
            "answers",
            f"removed_{datetime.now().timestamp()}_{question_id}.png",
        )
        os.rename(old, new_path)
    switch_image_flag(0, "answer", question_id)
    return {"ok": True}
