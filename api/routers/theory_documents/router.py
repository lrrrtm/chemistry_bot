import html
import json
import os
import uuid
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from api.config import ROOT_FOLDER
from api.dependencies import require_auth
from api.routers.theory_documents.schemas import TheoryDocumentUpdate
from db.crud import (
    create_theory_document,
    deactivate_theory_document,
    get_theory_document_by_id,
    get_theory_documents,
    replace_theory_document_file,
    update_theory_document,
)

router = APIRouter(tags=["theory-documents"])

_CACHE_HEADERS = {"Cache-Control": "public, max-age=86400"}
_THEORY_DIR = os.path.join(ROOT_FOLDER, "data", "theory_documents")


def _ensure_pdf(file: UploadFile) -> None:
    file_name = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()
    if not file_name.endswith(".pdf") and content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(status_code=400, detail="Разрешены только PDF-файлы")


def _parse_tags_json(raw_tags: str | None) -> list[str]:
    if not raw_tags:
        return []
    try:
        data = json.loads(raw_tags)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Некорректный формат tags_json") from exc
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="tags_json должен быть списком")
    return [str(value) for value in data]


def _document_path(file_name: str) -> str:
    return os.path.join(_THEORY_DIR, file_name)


def _serialize_document(document) -> dict:
    return {
        "id": document.id,
        "title": document.title,
        "tags_list": document.tags_list,
        "file_size": document.file_size,
        "mime_type": document.mime_type,
        "created_at": document.created_at.isoformat() if document.created_at else None,
    }


def _build_pdf_viewer_html(file_url: str, title: str) -> str:
    safe_title = html.escape(title)
    safe_file_url = html.escape(file_url, quote=True)
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <title>{safe_title}</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #161616;
      --panel: #202020;
      --text: #f4f4f4;
      --muted: rgba(255, 255, 255, 0.68);
      --accent: #39a8e8;
      --border: rgba(255, 255, 255, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; min-height: 100%; background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ display: flex; flex-direction: column; }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      background: rgba(22, 22, 22, 0.92);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid var(--border);
    }}
    .toolbar__meta {{ min-width: 0; }}
    .toolbar__title {{ margin: 0; font-size: 17px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .toolbar__hint {{ margin: 4px 0 0; color: var(--muted); font-size: 13px; }}
    .toolbar__link {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 40px;
      padding: 0 14px;
      border-radius: 999px;
      text-decoration: none;
      color: #fff;
      background: var(--accent);
      font-weight: 600;
      white-space: nowrap;
    }}
    .status {{
      padding: 20px 16px 4px;
      color: var(--muted);
      font-size: 14px;
      text-align: center;
    }}
    .pages {{
      width: min(980px, 100%);
      margin: 0 auto;
      padding: 12px 12px 24px;
    }}
    .page {{
      margin: 0 auto 16px;
      padding: 10px;
      border-radius: 18px;
      background: var(--panel);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.24);
    }}
    canvas {{
      display: block;
      width: 100%;
      height: auto;
      border-radius: 12px;
      background: #fff;
    }}
  </style>
</head>
<body>
  <div class="toolbar">
    <div class="toolbar__meta">
      <h1 class="toolbar__title">{safe_title}</h1>
      <p class="toolbar__hint">Документ открыт в режиме просмотра</p>
    </div>
    <a class="toolbar__link" href="{safe_file_url}" target="_blank" rel="noopener noreferrer">Скачать PDF</a>
  </div>

  <div id="status" class="status">Загружаем документ…</div>
  <div id="pages" class="pages" hidden></div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
  <script>
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

    const fileUrl = {json.dumps(file_url)};
    const statusNode = document.getElementById('status');
    const pagesNode = document.getElementById('pages');

    const setStatus = (text) => {{
      statusNode.textContent = text;
      statusNode.hidden = false;
    }};

    const showPages = () => {{
      pagesNode.hidden = false;
      statusNode.hidden = true;
    }};

    const render = async () => {{
      try {{
        const pdf = await pdfjsLib.getDocument({{ url: fileUrl, withCredentials: true }}).promise;
        const width = Math.min(window.innerWidth - 24, 956);
        for (let index = 1; index <= pdf.numPages; index += 1) {{
          setStatus(`Загружаем страницу ${{index}} из ${{pdf.numPages}}…`);
          const page = await pdf.getPage(index);
          const initialViewport = page.getViewport({{ scale: 1 }});
          const scale = width / initialViewport.width;
          const viewport = page.getViewport({{ scale }});
          const wrapper = document.createElement('div');
          wrapper.className = 'page';
          const canvas = document.createElement('canvas');
          const context = canvas.getContext('2d');
          canvas.width = viewport.width;
          canvas.height = viewport.height;
          wrapper.appendChild(canvas);
          pagesNode.appendChild(wrapper);
          await page.render({{ canvasContext: context, viewport }}).promise;
        }}
        showPages();
      }} catch (error) {{
        setStatus('Не удалось открыть документ. Попробуйте скачать PDF по кнопке сверху.');
      }}
    }};

    render();
  </script>
</body>
</html>"""


@router.get("/api/admin/theory-documents")
def list_theory_documents(
    query: str = Query(default="", alias="query"),
    _: str = Depends(require_auth),
):
    documents = get_theory_documents(active=False, query=query)
    return [_serialize_document(document) for document in documents if document.is_active]


@router.post("/api/admin/theory-documents")
def create_theory_document_endpoint(
    title: str = Form(...),
    tags_json: str = Form(default="[]"),
    file: UploadFile = File(...),
    _: str = Depends(require_auth),
):
    normalized_title = title.strip()
    if not normalized_title:
        raise HTTPException(status_code=400, detail="Введите название документа")

    _ensure_pdf(file)
    tags_list = _parse_tags_json(tags_json)
    os.makedirs(_THEORY_DIR, exist_ok=True)

    generated_file_name = f"{uuid.uuid4().hex}.pdf"
    file_bytes = file.file.read()

    document = create_theory_document(
        title=normalized_title,
        file_name=generated_file_name,
        original_file_name=file.filename,
        mime_type="application/pdf",
        file_size=len(file_bytes),
        tags_list=tags_list,
    )

    with open(_document_path(generated_file_name), "wb") as output:
        output.write(file_bytes)

    return {"ok": True, "document": _serialize_document(document)}


@router.put("/api/admin/theory-documents/{document_id}")
def update_theory_document_endpoint(
    document_id: int,
    payload: TheoryDocumentUpdate,
    _: str = Depends(require_auth),
):
    normalized_title = payload.title.strip()
    if not normalized_title:
        raise HTTPException(status_code=400, detail="Введите название документа")

    document = update_theory_document(
        document_id=document_id,
        title=normalized_title,
        tags_list=payload.tags_list,
    )
    if not document:
        raise HTTPException(status_code=404, detail="Документ не найден")

    return {"ok": True, "document": _serialize_document(document)}


@router.post("/api/admin/theory-documents/{document_id}/file")
def replace_theory_document_file_endpoint(
    document_id: int,
    file: UploadFile = File(...),
    _: str = Depends(require_auth),
):
    document = get_theory_document_by_id(document_id, active_only=False)
    if not document or not document.is_active:
        raise HTTPException(status_code=404, detail="Документ не найден")

    _ensure_pdf(file)
    os.makedirs(_THEORY_DIR, exist_ok=True)

    new_file_name = f"{uuid.uuid4().hex}.pdf"
    file_bytes = file.file.read()
    old_path = _document_path(document.file_name)

    updated = replace_theory_document_file(
        document_id=document_id,
        file_name=new_file_name,
        original_file_name=file.filename,
        mime_type="application/pdf",
        file_size=len(file_bytes),
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Документ не найден")

    with open(_document_path(new_file_name), "wb") as output:
        output.write(file_bytes)

    if os.path.exists(old_path):
        os.remove(old_path)

    return {"ok": True, "document": _serialize_document(updated)}


@router.delete("/api/admin/theory-documents/{document_id}")
def delete_theory_document_endpoint(document_id: int, _: str = Depends(require_auth)):
    document = get_theory_document_by_id(document_id, active_only=False)
    if not document:
        raise HTTPException(status_code=404, detail="Документ не найден")

    deactivate_theory_document(document_id)
    return {"ok": True}


@router.get("/api/theory-documents/{document_id}/file")
def get_theory_document_file(document_id: int):
    document = get_theory_document_by_id(document_id, active_only=True)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    path = _document_path(document.file_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    visible_name = (document.original_file_name or f"{document.title}.pdf").replace('"', "")
    headers = {
        **_CACHE_HEADERS,
        "Content-Disposition": f"inline; filename*=UTF-8''{quote(visible_name)}",
    }
    return FileResponse(path, media_type=document.mime_type, headers=headers)


@router.get("/api/theory-documents/{document_id}/view")
def view_theory_document(document_id: int, request: Request):
    document = get_theory_document_by_id(document_id, active_only=True)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    path = _document_path(document.file_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    file_url = str(request.url_for("get_theory_document_file", document_id=document_id))
    visible_name = document.title or document.original_file_name or "Документ"
    return HTMLResponse(_build_pdf_viewer_html(file_url=file_url, title=visible_name))
