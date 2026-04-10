from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import require_auth
from api.routers.student_auth.service import (
    ACCESS_GRANT_PURPOSE_ADMIN_INVITE,
    ACCESS_GRANT_PURPOSE_SELF_WEB_ACCESS,
    generate_one_time_token,
    hash_one_time_token,
    invite_expiration,
)
from db.crud import (
    create_invited_user,
    get_all_users,
    get_user_by_id,
    issue_student_access_grant,
    remove_user,
    rename_user,
)
from utils.mini_app_links import get_tma_invite_url
from utils.user_statistics import get_user_statistics_by_user_id

router = APIRouter(prefix="/api/admin/users", tags=["users"])


def _serialize_user(user):
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "name": user.name,
        "username": user.username,
        "has_credentials": bool(user.username and user.password_hash),
        "telegram_linked": bool(user.telegram_id),
    }


def _issue_web_access_grant(
    user_id: int,
    *,
    purpose: str,
    created_by: str,
    require_missing_credentials: bool = False,
) -> dict:
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Ученик не найден")
    if require_missing_credentials and user.username and user.password_hash:
        raise HTTPException(status_code=409, detail="Веб-доступ уже настроен")

    raw_token = generate_one_time_token()
    expires_at = invite_expiration()
    grant = issue_student_access_grant(
        user_id=user_id,
        purpose=purpose,
        token_hash=hash_one_time_token(raw_token),
        expires_at=expires_at,
        created_by=created_by,
    )
    if not grant:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    return {
        "user": _serialize_user(user),
        "invite_token": raw_token,
        "invite_url": get_tma_invite_url(raw_token),
        "invite_expires_at": expires_at.isoformat(),
    }


def _issue_admin_invite(user_id: int) -> dict:
    return _issue_web_access_grant(
        user_id,
        purpose=ACCESS_GRANT_PURPOSE_ADMIN_INVITE,
        created_by="admin",
    )


@router.get("")
def list_users(_: str = Depends(require_auth)):
    users = get_all_users()
    return [_serialize_user(user) for user in sorted(users, key=lambda item: item.name.lower())]


@router.post("")
def create_user_endpoint(body: dict, _: str = Depends(require_auth)):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Имя не может быть пустым")

    user = create_invited_user(name=name)
    return _issue_admin_invite(user.id)


@router.post("/{user_id}/invite")
def regenerate_invite(user_id: int, _: str = Depends(require_auth)):
    return _issue_admin_invite(user_id)


@router.post("/{user_id}/web-access-link")
def issue_web_access_link(user_id: int, _: str = Depends(require_auth)):
    return _issue_web_access_grant(
        user_id,
        purpose=ACCESS_GRANT_PURPOSE_SELF_WEB_ACCESS,
        created_by="admin_web_access",
        require_missing_credentials=True,
    )


@router.put("/{user_id}")
def update_user(user_id: int, body: dict, _: str = Depends(require_auth)):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Имя не может быть пустым")
    rename_user(user_id=user_id, new_name=name)
    return {"ok": True}


@router.delete("/{user_id}")
def delete_user(user_id: int, _: str = Depends(require_auth)):
    remove_user(user_id=user_id)
    return {"ok": True}


@router.get("/{user_id}/stats")
def user_stats(user_id: int, _: str = Depends(require_auth)):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    stats = get_user_statistics_by_user_id(user_id)
    return [
        {
            "work_id": stat["general"]["work_id"],
            "share_token": stat["general"].get("share_token"),
            "name": stat["general"]["name"],
            "type": stat["general"]["type"],
            "start": stat["general"]["time"]["start"].isoformat(),
            "end": stat["general"]["time"]["end"].isoformat(),
            "final_mark": stat["results"]["final_mark"],
            "max_mark": stat["results"]["max_mark"],
            "fully": len(stat["questions"]["fully"]),
            "semi": len(stat["questions"]["semi"]),
            "zero": len(stat["questions"]["zero"]),
            "questions_amount": stat["general"].get("questions_amount", 0),
        }
        for stat in stats
    ]
