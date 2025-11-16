from __future__ import annotations

import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml
from PIL import Image

from .config import get_assets_dir, get_images_dir, get_templates_config_path
from .input import ClickPadding, pick_point
from .vision import MatchResult, match_template

SearchRegion = Dict[str, float]


def _load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def _region_to_absolute(region: Optional[SearchRegion], window_size: Tuple[int, int]) -> Optional[Tuple[int, int, int, int]]:
    if not region:
        return None
    if region.get("type") != "relative":
        return None
    x = int(region.get("x", 0) * window_size[0])
    y = int(region.get("y", 0) * window_size[1])
    w = int(region.get("width", 1) * window_size[0])
    h = int(region.get("height", 1) * window_size[1])
    return x, y, w, h


@dataclass
class Template:
    key: str
    file: Path
    description: str = ""
    threshold: float = 0.85
    method: str = "TM_CCOEFF_NORMED"
    search_region: Optional[SearchRegion] = None
    click_mode: str = "center"
    padding: ClickPadding = field(default_factory=ClickPadding)

    def load_image(self) -> Image.Image:
        return _load_image(self.file)

    def find(self, image, window_size: Tuple[int, int]) -> Optional[MatchResult]:
        region = _region_to_absolute(self.search_region, window_size)
        return match_template(
            image=image,
            template=self.load_image(),
            threshold=self.threshold,
            region=region,
            method=self.method,
        )

    def coord(self, match_rect: Optional[Tuple[int, int, int, int]] = None) -> Tuple[int, int]:
        if not match_rect:
            return 0, 0
        return pick_point(match_rect, mode=self.click_mode, padding=self.padding)


class ImageTemplate(Template):
    pass


class ClickTemplate(Template):
    pass


class LongClickTemplate(Template):
    def __post_init__(self):
        self.click_mode = "center"


class SwipeTemplate(Template):
    # For swipe we still reuse template matching but higher-level code handles movement.
    pass


class OcrTemplate(Template):
    # OCR is stubbed; extend later with actual OCR engine.
    pass


class ListTemplate(Template):
    pass


def _padding_from_dict(data: Dict) -> ClickPadding:
    return ClickPadding(
        left=float(data.get("left", 0)),
        right=float(data.get("right", 0)),
        top=float(data.get("top", 0)),
        bottom=float(data.get("bottom", 0)),
    )


def template_from_definition(key: str, definition: Dict, assets_dir: Path | None = None) -> Template:
    """
    Resolve template config to Template instance.

    If file is absolute, keep it; otherwise always resolve relative to the
    templates.yaml directory (assets_dir). The previous behavior forced
    paths like images/foo.png back to the global assets dir, causing task
    templates to ignore updated images in their own folders.
    """
    assets_dir = assets_dir or get_images_dir()
    clazz = definition.get("type", "click").lower()
    cls_map = {
        "image": ImageTemplate,
        "click": ClickTemplate,
        "longclick": LongClickTemplate,
        "swipe": SwipeTemplate,
        "ocr": OcrTemplate,
        "list": ListTemplate,
    }
    cls = cls_map.get(clazz, Template)
    raw_file = Path(definition["file"])
    if raw_file.is_absolute():
        file_path = raw_file
    else:
        # Always resolve relative to the templates.yaml folder (assets_dir)
        # so per-task images (tasks/<id>/images/xxx.png) are respected.
        file_path = Path(assets_dir) / raw_file
    padding = _padding_from_dict(definition.get("click", {}).get("padding", {})) if definition.get("click") else ClickPadding()
    return cls(
        key=key,
        file=file_path,
        description=definition.get("description", ""),
        threshold=float(definition.get("match", {}).get("threshold", 0.85)),
        method=definition.get("match", {}).get("method", "TM_CCOEFF_NORMED"),
        search_region=definition.get("search_region"),
        click_mode=definition.get("click", {}).get("mode", "center"),
        padding=padding,
    )


def load_templates(config_path: Path | str | os.PathLike | None = None) -> Dict[str, Template]:
    if config_path and not isinstance(config_path, Path):
        config_path = Path(config_path)
    path: Path = config_path or get_templates_config_path()
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    templates: Dict[str, Template] = {}
    for key, definition in (data.get("templates") or {}).items():
        try:
            templates[key] = template_from_definition(key, definition, assets_dir=path.parent)
        except Exception:
            # Skip malformed entries to avoid hard crashes.
            continue
    return templates
