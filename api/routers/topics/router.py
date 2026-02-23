import os

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from api.config import ROOT_FOLDER
from api.dependencies import require_auth
from api.routers.topics.schemas import TopicCreate, TopicTagsUpdate
from db.crud import (
    create_topic,
    deactivate_topic,
    get_all_pool,
    get_all_topics,
    get_topics_table,
    insert_topics_data,
    update_topic,
)
from utils.clearing import clear_folder
from utils.excel import export_topics_list, import_topics_list

router = APIRouter(prefix="/api/admin/topics", tags=["topics"])


@router.get("")
def list_topics(_: str = Depends(require_auth)):
    topics = get_topics_table()
    pool = get_all_pool(active=True)

    tag_counter: dict = {}
    for q in pool:
        for tag in q.tags_list:
            tag_counter[tag] = tag_counter.get(tag, 0) + 1

    result: dict = {}
    for t in topics:
        if t.volume not in result:
            result[t.volume] = []
        result[t.volume].append(
            {
                "id": t.id,
                "name": t.name,
                "tags": [
                    {"tag": tag, "count": tag_counter.get(tag, 0)}
                    for tag in sorted(t.tags_list)
                ],
            }
        )
    return result


@router.post("")
def create_topic_endpoint(req: TopicCreate, _: str = Depends(require_auth)):
    t = create_topic(req.name, req.volume)
    return {"id": t.id, "name": t.name, "volume": t.volume, "tags": []}


@router.delete("/{topic_id}")
def delete_topic_endpoint(topic_id: int, _: str = Depends(require_auth)):
    deactivate_topic(topic_id)
    return {"ok": True}


@router.put("/{topic_id}")
def update_topic_endpoint(
    topic_id: int, req: TopicTagsUpdate, _: str = Depends(require_auth)
):
    update_topic(topic_id, req.tags_list)
    return {"ok": True}


@router.get("/export")
def export_topics_excel(_: str = Depends(require_auth)):
    topics_list = get_all_topics(active=True)
    export_topics_list(topics_list)
    filepath = os.path.join(ROOT_FOLDER, "data", "temp", "chembot_topics_list.xlsx")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="chembot_topics_list.xlsx",
    )


@router.post("/import")
def import_topics_excel(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    _: str = Depends(require_auth),
):
    from datetime import datetime

    filepath = os.path.join(
        ROOT_FOLDER,
        "data",
        "temp",
        f"topics_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx",
    )
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(file.file.read())

    import_data = import_topics_list(filepath)

    if not import_data["is_ok"]:
        clear_folder(os.path.join(ROOT_FOLDER, "data", "temp"))
        raise HTTPException(status_code=400, detail=import_data["comment"])

    insert_topics_data(import_data["data"])
    background_tasks.add_task(clear_folder, os.path.join(ROOT_FOLDER, "data", "temp"))
    return {"ok": True, "message": import_data["comment"]}
