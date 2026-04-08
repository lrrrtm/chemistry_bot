from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from api.routers.auth.service import verify_token
from api.routers.student_auth.service import verify_student_token
from db.crud import get_user_by_id


def require_auth(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not verify_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return token


def require_student_auth(x_student_token: Optional[str] = Header(None)) -> int:
    if not x_student_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing student token",
        )

    token_data = verify_student_token(x_student_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired student token",
        )

    user_id, token_version = token_data
    user = get_user_by_id(user_id)
    if not user or (user.student_token_version or 0) != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired student token",
        )

    return user_id
