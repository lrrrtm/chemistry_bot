from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import require_auth
from db.crud import get_all_users, remove_user, rename_user
from utils.user_statistics import get_user_statistics

router = APIRouter(prefix="/api/admin/users", tags=["users"])


@router.get("")
def list_users(_: str = Depends(require_auth)):
    users = get_all_users()
    return [
        {"id": u.id, "telegram_id": u.telegram_id, "name": u.name}
        for u in sorted(users, key=lambda u: u.name)
    ]


@router.put("/{telegram_id}")
def update_user(telegram_id: int, body: dict, _: str = Depends(require_auth)):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Имя не может быть пустым")
    rename_user(telegram_id=telegram_id, new_name=name)
    return {"ok": True}


@router.delete("/{telegram_id}")
def delete_user(telegram_id: int, _: str = Depends(require_auth)):
    remove_user(telegram_id=telegram_id)
    return {"ok": True}


@router.get("/{telegram_id}/stats")
def user_stats(telegram_id: int, _: str = Depends(require_auth)):
    stats = get_user_statistics(telegram_id)
    return [
        {
            "work_id": s["general"]["work_id"],
            "share_token": s["general"].get("share_token"),
            "name": s["general"]["name"],
            "type": s["general"]["type"],
            "start": s["general"]["time"]["start"].isoformat(),
            "end": s["general"]["time"]["end"].isoformat(),
            "final_mark": s["results"]["final_mark"],
            "max_mark": s["results"]["max_mark"],
            "fully": len(s["questions"]["fully"]),
            "semi": len(s["questions"]["semi"]),
            "zero": len(s["questions"]["zero"]),
            "questions_amount": s["general"].get("questions_amount", 0),
        }
        for s in stats
    ]
