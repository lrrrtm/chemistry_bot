import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.config import ROOT_FOLDER

router = APIRouter(prefix="/api/images", tags=["images"])

_CACHE_HEADERS = {"Cache-Control": "public, max-age=86400"}


@router.get("/question/{question_id}")
def get_question_image(question_id: int):
    path = os.path.join(ROOT_FOLDER, "data", "images", "questions", f"{question_id}.png")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/png", headers=_CACHE_HEADERS)


@router.get("/answer/{question_id}")
def get_answer_image(question_id: int):
    path = os.path.join(ROOT_FOLDER, "data", "images", "answers", f"{question_id}.png")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/png", headers=_CACHE_HEADERS)


@router.get("/user/{telegram_id}")
def get_user_photo(telegram_id: int):
    path = os.path.join(ROOT_FOLDER, "data", "images", "users", f"{telegram_id}.jpg")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(path, media_type="image/jpeg", headers=_CACHE_HEADERS)
