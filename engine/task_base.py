from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image

from . import config
from .capture import capture_window
from .input import InputController
from .logging import log_store
from .templates import Template, load_templates
from .vision import MatchResult
from .window import TargetWindowConfig, activate_window, find_window, get_window_rect


class TaskBase:
    def __init__(
        self,
        target_window: Optional[TargetWindowConfig] = None,
        template_config_path: Optional[Path] = None,
    ) -> None:
        self.target_window_config = target_window
        self.hwnd: Optional[int] = None
        self.template_config_path = template_config_path
        self.templates: Dict[str, Template] = load_templates(template_config_path)
        self._last_image: Optional[Image.Image] = None
        self._input = InputController(self._get_window_rect)

    # Window helpers
    def _ensure_hwnd(self) -> Optional[int]:
        if self.hwnd and self.hwnd > 0:
            return self.hwnd
        if not self.target_window_config:
            raise RuntimeError("未绑定目标窗口，请先在任务配置中绑定窗口句柄")
        self.hwnd = find_window(self.target_window_config)
        return self.hwnd

    def get_window(self) -> Optional[int]:
        return self._ensure_hwnd()

    def _get_window_rect(self):
        hwnd = self._ensure_hwnd()
        if not hwnd:
            raise RuntimeError("Target window not resolved")
        return get_window_rect(hwnd)

    def ensure_window_focused(self) -> None:
        hwnd = self._ensure_hwnd()
        if not hwnd:
            raise RuntimeError("Target window not found")
        activate_window(hwnd)

    # Screenshots and template resolution
    def screenshot(self) -> Image.Image:
        hwnd = self._ensure_hwnd()
        if not hwnd:
            raise RuntimeError("Target window not found")
        self._last_image = capture_window(hwnd)
        return self._last_image

    def resolve_template(self, template_or_key) -> Template:
        # Always reload templates to reflect latest edits
        self.templates = load_templates(self.template_config_path)
        if isinstance(template_or_key, Template):
            return template_or_key
        key = str(template_or_key)
        if key not in self.templates:
            raise KeyError(f"Template '{key}' not found")
        return self.templates[key]

    def _match(self, template: Template, threshold: Optional[float] = None) -> Optional[MatchResult]:
        # Always use最新截图避免旧图导致误判/重复点击
        self.screenshot()
        window_rect = self._get_window_rect()
        w = window_rect[2] - window_rect[0]
        h = window_rect[3] - window_rect[1]
        tpl = template
        tpl.threshold = threshold or tpl.threshold
        return tpl.find(self._last_image, (w, h))

    # Public APIs for scripts
    def appear(self, template_or_key, threshold: Optional[float] = None) -> bool:
        template = self.resolve_template(template_or_key)
        return self._match(template, threshold) is not None

    def wait_appear(self, template_or_key, timeout: float = 10, interval: float = 0.5, threshold: Optional[float] = None) -> bool:
        start = time.time()
        while time.time() - start <= timeout:
            if self.appear(template_or_key, threshold=threshold):
                return True
            time.sleep(interval)
            self.screenshot()
        return False

    def disappear(self, template_or_key, timeout: float = 10, interval: float = 0.5) -> bool:
        start = time.time()
        while time.time() - start <= timeout:
            if not self.appear(template_or_key):
                return True
            time.sleep(interval)
            self.screenshot()
        return False

    def click_template(self, template_or_key, threshold: Optional[float] = None, interval: float = 0.2) -> bool:
        template = self.resolve_template(template_or_key)
        match = self._match(template, threshold)
        if not match:
            self.log(f"未匹配到模板: {template.key}", level="WARN")
            return False
        self._input.click_rect(
            match.rect,
            mode=template.click_mode,
            padding=template.padding,
            interval=interval,
        )
        return True

    def appear_then_click(
        self,
        template_or_key,
        timeout: float = 5,
        interval: float = 0.5,
        threshold: Optional[float] = None,
    ) -> bool:
        if not self.wait_appear(template_or_key, timeout=timeout, interval=interval, threshold=threshold):
            return False
        return self.click_template(template_or_key, threshold=threshold, interval=interval)

    def read_text(self, _template_or_key) -> str:
        # OCR placeholder: in a real implementation, tie into OCR engine.
        return ""

    def sleep(self, sec: float) -> None:
        time.sleep(sec)

    def log(self, msg: str, level: str = "INFO") -> None:
        log_store.log(msg, level=level, task_id=self.__class__.__name__)

    # Entry point to override
    def run(self, context: Optional[Dict[str, Any]] = None) -> None:
        raise NotImplementedError("TaskBase subclasses must implement run()")


def load_task_from_module(module_path: Path, entry: str):
    module_name = module_path.with_suffix("").as_posix().replace("/", ".").replace("\\", ".")
    if module_name.startswith("."):
        module_name = module_name[1:]
    module = importlib.import_module(module_name)
    target = getattr(module, entry)
    if isinstance(target, type):
        return target()
    return target
