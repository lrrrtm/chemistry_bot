import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# config.py добавляет корень проекта в sys.path и загружает .env
import api.config  # noqa: F401

from api.scheduler import lifespan
from api.routers.auth.router import router as auth_router
from api.routers.backup.router import router as backup_router
from api.routers.ege.router import router as ege_router
from api.routers.hand_works.router import router as hand_works_router
from api.routers.images.router import router as images_router
from api.routers.pool.router import router as pool_router
from api.routers.student.router import router as student_router
from api.routers.student_auth.router import router as student_auth_router
from api.routers.tma.router import router as tma_router
from api.routers.theory_documents.router import router as theory_documents_router
from api.routers.topics.router import router as topics_router
from api.routers.users.router import router as users_router

app = FastAPI(title="ChemBot Admin API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(images_router)
app.include_router(users_router)
app.include_router(student_router)
app.include_router(student_auth_router)
app.include_router(tma_router)
app.include_router(theory_documents_router)
app.include_router(topics_router)
app.include_router(hand_works_router)
app.include_router(pool_router)
app.include_router(ege_router)
app.include_router(backup_router)

# ── Serve TMA (Mini App) at /tma/ ─────────────────────────────────────────────
# Must be registered BEFORE the admin SPA catch-all below.
TMA_DIST = os.path.join(os.path.dirname(__file__), "..", "tma", "dist")
if os.path.isdir(TMA_DIST):
    _tma_assets = os.path.join(TMA_DIST, "assets")
    if os.path.isdir(_tma_assets):
        app.mount("/tma/assets", StaticFiles(directory=_tma_assets), name="tma-assets")

    @app.get("/tma/{full_path:path}", include_in_schema=False)
    def serve_tma(full_path: str):
        candidate = os.path.join(TMA_DIST, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(TMA_DIST, "index.html"))

    @app.get("/tma", include_in_schema=False)
    def serve_tma_root():
        return FileResponse(os.path.join(TMA_DIST, "index.html"))

# ── Serve Admin SPA (catch-all) ───────────────────────────────────────────────
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    _assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
