import os

from fastapi import APIRouter, Depends, HTTPException

import api.config as _config
from api.dependencies import require_auth
from api.routers.auth.schemas import LoginRequest, LoginResponse
from api.routers.auth.service import (
    create_token,
    generate_password,
    send_password_to_admin,
    update_env_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    if req.password != _config.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Неверный пароль")
    return {"token": create_token("admin")}


@router.get("/verify")
def verify(_: str = Depends(require_auth)):
    return {"ok": True}


@router.post("/recover-password")
def recover_password():
    new_password = generate_password()
    try:
        send_password_to_admin(new_password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    env_path = os.path.join(_config.ROOT_FOLDER, ".env")
    update_env_password(new_password, env_path)

    os.environ["PANEL_PASSWORD"] = new_password
    _config.SECRET_KEY = new_password

    return {"ok": True}
