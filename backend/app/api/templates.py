from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from PIL import Image

from engine import config as engine_config
from engine.logging import log_store
from engine.templates import load_templates
from engine.vision import match_template

from ..models.schemas import SaveTemplateRequest, TemplateDefinitionModel, TemplateTestRequest

router = APIRouter(prefix="/api/templates")


def _load_config(path: Path) -> Dict:
    if not path.exists():
        return {"templates": {}}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"templates": {}}


@router.get("/", response_model=Dict[str, TemplateDefinitionModel])
def list_templates(task_id: Optional[str] = None):
    config_path = None
    if task_id:
        config_path = engine_config.get_tasks_root() / task_id / "templates.yaml"
    templates = load_templates(config_path=config_path)
    result: Dict[str, TemplateDefinitionModel] = {}
    for key, tpl in templates.items():
        result[key] = TemplateDefinitionModel(
            key=key,
            file=str(Path(tpl.file).as_posix()),
            description=tpl.description,
            match={"threshold": tpl.threshold, "method": tpl.method},
            search_region=tpl.search_region,
            click={
                "mode": tpl.click_mode,
                "padding": {
                    "left": tpl.padding.left,
                    "right": tpl.padding.right,
                    "top": tpl.padding.top,
                    "bottom": tpl.padding.bottom,
                },
            },
            type=tpl.__class__.__name__.replace("Template", "").lower() or "click",
        )
    return result


@router.post("/", response_model=TemplateDefinitionModel)
def save_template(request: SaveTemplateRequest):
    base_image_path = Path(request.base_image_path)
    if not base_image_path.exists():
        raise HTTPException(status_code=404, detail="base image not found")

    base_image = Image.open(base_image_path)
    width, height = base_image.size

    def _rect_to_box(rect):
        x = int(rect.x * width)
        y = int(rect.y * height)
        w = int(rect.width * width)
        h = int(rect.height * height)
        return (x, y, x + w, y + h)

    crop_box = _rect_to_box(request.template_rect)
    cropped = base_image.crop(crop_box)

    output_name = f"{request.key}.png"
    subdir = request.task_id.strip() if request.task_id else None
    base_dir = engine_config.get_images_dir()
    if subdir:
        base_dir = engine_config.get_tasks_root() / subdir / "images"
    save_dir = base_dir
    save_path = save_dir / output_name
    save_path.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(save_path)

    config_path = engine_config.get_templates_config_path()
    if subdir:
        config_path = engine_config.get_tasks_root() / subdir / "templates.yaml"

    data = _load_config(config_path)
    data.setdefault("templates", {})
    data["templates"][request.key] = {
        "file": str(Path(save_path).relative_to(config_path.parent).as_posix()),
        "description": request.description,
        "match": {"threshold": request.threshold, "method": request.match_method},
        "search_region": request.search_region.dict() if request.search_region else None,
        "click": {
            "mode": request.click_mode,
            "padding": request.padding.dict(),
        },
        "type": "click",
        "task_id": request.task_id,
    }
    config_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    return TemplateDefinitionModel(
        key=request.key,
        file=str(Path(save_path).relative_to(config_path.parent).as_posix()),
        description=request.description,
        match={"threshold": request.threshold, "method": request.match_method},
        search_region=request.search_region,
        click={"mode": request.click_mode, "padding": request.padding},
        type="click",
    )


@router.post("/upload-base")
def upload_base(task_id: Optional[str] = None, file: UploadFile = File(...)):
    base_dir = engine_config.get_images_dir() / "base_uploads"
    if task_id:
        base_dir = engine_config.get_tasks_root() / task_id / "images"
    base_dir.mkdir(parents=True, exist_ok=True)
    filename = f"base_{int(time.time())}_{file.filename}"
    save_path = base_dir / filename
    content = file.file.read()
    save_path.write_bytes(content)
    return {"path": str(save_path)}


def _abs_region(search_region, size: Tuple[int, int]) -> Optional[Tuple[int, int, int, int]]:
    if not search_region:
        return None
    if search_region.get("type") != "relative":
        return None
    return (
        int(search_region["x"] * size[0]),
        int(search_region["y"] * size[1]),
        int(search_region["width"] * size[0]),
        int(search_region["height"] * size[1]),
    )


@router.post("/test")
def test_template(request: TemplateTestRequest, task_id: Optional[str] = None):
    config_path = None
    if task_id:
        config_path = engine_config.get_tasks_root() / task_id / "templates.yaml"
    templates = load_templates(config_path=config_path)
    tpl = templates.get(request.key)
    if not tpl:
        raise HTTPException(status_code=404, detail="template not found")
    base_image_path = Path(request.base_image_path)
    if not base_image_path.exists():
        raise HTTPException(status_code=404, detail="test base image not found")
    base_image = Image.open(base_image_path)
    size = base_image.size
    region = _abs_region(tpl.search_region, size)
    result = match_template(
        image=base_image,
        template=tpl.load_image(),
        threshold=tpl.threshold,
        region=region,
        method=tpl.method,
    )
    if not result:
        log_store.log(f"[TEST] {request.key} not matched in {request.base_image_path}", level="TEST", task_id="template_test")
        return {"matched": False}
    click_point = tpl.coord(result.rect)
    log_store.log(
        f"[TEST] {request.key} matched. conf={result.confidence:.3f}, click={click_point}",
        level="TEST",
        task_id="template_test",
    )
    return {
        "matched": True,
        "confidence": result.confidence,
        "rect": {"x": result.rect[0], "y": result.rect[1], "width": result.rect[2], "height": result.rect[3]},
        "click_point": {"x": click_point[0], "y": click_point[1]},
        "image_size": {"width": size[0], "height": size[1]},
    }


@router.get("/base-image")
def get_base_image(path: str):
    p = Path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="image not found")
    data = p.read_bytes()
    return Response(content=data, media_type="image/png")
