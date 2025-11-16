from __future__ import annotations

import sys
from pathlib import Path
from app.utils.pydantic_patch import apply_forwardref_patch
apply_forwardref_patch()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from engine import config as engine_config

from .api import logs, tasks, templates, windows

app = FastAPI(title="WinAutoClick Framework", version="0.1.0")

app.include_router(windows.router)
app.include_router(templates.router)
app.include_router(tasks.router)
app.include_router(logs.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


frontend_dir: Path = engine_config.get_frontend_dir()
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.get("/")
def root():
    index = frontend_dir / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Frontend not built yet. Run npm install && npm run dev in ui/."}
