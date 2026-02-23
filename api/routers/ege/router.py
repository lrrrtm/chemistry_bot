from fastapi import APIRouter, Depends

from api.dependencies import require_auth
from api.routers.ege.schemas import EgeConvertingUpdate
from db.crud import get_ege_converting, update_ege_converting

router = APIRouter(prefix="/api/admin/ege-converting", tags=["ege"])


@router.get("")
def ege_converting(_: str = Depends(require_auth)):
    data = get_ege_converting()
    return [
        {"id": el.id, "input_mark": el.input_mark, "output_mark": el.output_mark}
        for el in data
    ]


@router.put("")
def update_ege(req: EgeConvertingUpdate, _: str = Depends(require_auth)):
    config = {int(k): {"value": int(v), "is_ok": True} for k, v in req.data.items()}
    update_ege_converting(config)
    return {"ok": True}
