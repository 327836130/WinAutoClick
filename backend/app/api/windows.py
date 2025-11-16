from __future__ import annotations

import time
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException

from engine import config as engine_config
from engine import window as window_engine
from engine.capture import capture_window
from engine.window import TargetWindowConfig

from ..models.schemas import TargetWindowConfigModel

router = APIRouter(prefix="/api")


@router.get("/windows/", response_model=List[dict])
def list_windows():
    return window_engine.list_windows()


@router.post("/window/select", response_model=TargetWindowConfigModel)
def select_window(cfg: TargetWindowConfigModel):
    target = TargetWindowConfig(
        title_contains=cfg.title_contains,
        process_name=cfg.process_name,
        hwnd=cfg.hwnd,
    )
    hwnd = window_engine.find_window(target)
    if not hwnd:
        raise HTTPException(status_code=404, detail="没有找到符合条件的窗口")
    return TargetWindowConfigModel(title_contains=cfg.title_contains, process_name=cfg.process_name, hwnd=hwnd)


@router.post("/window/{hwnd}/screenshot-base")
def screenshot_base(hwnd: int):
    if not window_engine.window_exists(hwnd):
        raise HTTPException(status_code=404, detail="窗口不存在")
    image = capture_window(hwnd)
    filename = f"base_{hwnd}_{int(time.time())}.png"
    save_path: Path = engine_config.get_images_dir() / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(save_path)
    return {"path": str(save_path)}
