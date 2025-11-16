from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False) is True


def get_base_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_assets_dir() -> Path:
    return get_base_dir() / "assets"


def get_images_dir() -> Path:
    return get_assets_dir() / "images"


def get_templates_config_path() -> Path:
    return get_assets_dir() / "templates.yaml"


def get_scripts_dir() -> Path:
    return get_base_dir() / "scripts"


def get_frontend_dir() -> Path:
    base = get_base_dir()
    packaged = base / "frontend"
    dev_dist = base / "ui" / "dist"
    return packaged if packaged.exists() else dev_dist


def get_tasks_root() -> Path:
    return get_base_dir() / "tasks"
