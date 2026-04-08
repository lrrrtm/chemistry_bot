import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import require_student_auth
from api.routers.student_auth.service import (
    WEB_ACCESS_GRANT_PURPOSES,
    create_student_token,
    generate_one_time_token,
    hash_one_time_token,
    hash_password,
    normalize_username,
    telegram_link_expiration,
    validate_password,
    verify_password,
)
from db.crud import (
    activate_user_credentials,
    get_student_access_grant_by_token_hash,
    get_user_by_id,
    get_user_by_username,
    revoke_student_access_grants,
    set_telegram_link_token,
)

router = APIRouter(prefix="/api/student-auth", tags=["student_auth"])


class ActivateInviteBody(BaseModel):
    invite_token: str
    username: str
    password: str


class LoginBody(BaseModel):
    username: str
    password: str


def _serialize_profile(user):
    return {
        "registered": True,
        "auth_mode": "web",
        "user_id": user.id,
        "telegram_id": user.telegram_id,
        "telegram_linked": bool(user.telegram_id),
        "has_web_credentials": bool(user.username and user.password_hash),
        "name": user.name,
        "username": user.username,
    }


def _resolve_web_access_grant(raw_token: str):
    grant = get_student_access_grant_by_token_hash(hash_one_time_token(raw_token))
    if not grant or grant.purpose not in WEB_ACCESS_GRANT_PURPOSES:
        raise HTTPException(status_code=404, detail="Инвайт не найден")

    user = get_user_by_id(grant.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    if grant.expires_at and grant.expires_at < datetime.now():
        raise HTTPException(status_code=410, detail="Инвайт уже истёк")

    return user, grant


@router.get("/invite/{invite_token}")
def inspect_invite(invite_token: str):
    user, grant = _resolve_web_access_grant(invite_token)
    if grant.consumed_at or (user.username and user.password_hash):
        raise HTTPException(status_code=409, detail="Веб-доступ уже настроен. Используйте логин и пароль.")

    return {
        "name": user.name,
        "expires_at": grant.expires_at.isoformat() if grant.expires_at else None,
    }


@router.post("/activate")
def activate_invite(body: ActivateInviteBody):
    user, grant = _resolve_web_access_grant(body.invite_token)
    if grant.consumed_at or (user.username and user.password_hash):
        raise HTTPException(status_code=409, detail="Веб-доступ уже настроен. Используйте логин и пароль.")

    try:
        username = normalize_username(body.username)
        password = validate_password(body.password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    occupied = get_user_by_username(username)
    if occupied and occupied.id != user.id:
        raise HTTPException(status_code=409, detail="Такой логин уже занят")

    updated_user = activate_user_credentials(
        user_id=user.id,
        username=username,
        password_hash=hash_password(password),
    )
    if not updated_user:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    revoke_student_access_grants(user.id)

    return {
        "token": create_student_token(updated_user.id, updated_user.student_token_version or 0),
        "profile": _serialize_profile(updated_user),
    }


@router.post("/login")
def login(body: LoginBody):
    try:
        username = normalize_username(body.username)
        password = validate_password(body.password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    user = get_user_by_username(username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    return {
        "token": create_student_token(user.id, user.student_token_version or 0),
        "profile": _serialize_profile(user),
    }


@router.get("/me")
def me(user_id: int = Depends(require_student_auth)):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Ученик не найден")
    return _serialize_profile(user)


@router.post("/telegram-link/start")
def start_telegram_link(user_id: int = Depends(require_student_auth)):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Ученик не найден")
    if user.telegram_id:
        return {
            "ok": True,
            "linked": True,
            "bot_url": None,
        }

    raw_token = generate_one_time_token()
    expires_at = telegram_link_expiration()
    set_telegram_link_token(user.id, hash_one_time_token(raw_token), expires_at)

    bot_name = (os.getenv("BOT_NAME") or "").strip().lstrip("@")
    if not bot_name:
        raise HTTPException(status_code=500, detail="BOT_NAME не настроен")

    return {
        "ok": True,
        "linked": False,
        "bot_url": f"https://t.me/{bot_name}?start=link_{raw_token}",
        "expires_at": expires_at.isoformat(),
    }

