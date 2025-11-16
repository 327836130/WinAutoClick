from __future__ import annotations

import importlib
import threading
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

from .config import get_scripts_dir
from .logging import log_store
from .task_base import TaskBase
from .window import TargetWindowConfig


@dataclass
class TaskDefinition:
    id: str
    name: str
    script: str
    entry: str
    path: Optional[str] = None
    templates_path: Optional[str] = None
    target_window: Optional[TargetWindowConfig] = None


class TaskExecutor:
    def __init__(self) -> None:
        self._threads: Dict[str, threading.Thread] = {}

    def _build_instance(self, task_def: TaskDefinition) -> TaskBase:
        module_path = Path(task_def.script)
        if not module_path.is_absolute():
            module_path = get_scripts_dir() / module_path
        # 支持绝对路径脚本：将其父目录加入 sys.path，再按模块名导入
        module_name = module_path.stem
        if str(module_path.parent) not in sys.path:
            sys.path.insert(0, str(module_path.parent))
        module = importlib.import_module(module_name)
        cls_or_func = getattr(module, task_def.entry)
        if isinstance(cls_or_func, type):
            return cls_or_func(target_window=task_def.target_window, template_config_path=Path(task_def.templates_path) if task_def.templates_path else None)
        if isinstance(cls_or_func, Callable):
            # Wrap function into TaskBase-like runner
            class FuncTask(TaskBase):
                def run(self, context=None):
                    return cls_or_func(self, context=context)

            return FuncTask(target_window=task_def.target_window, template_config_path=Path(task_def.templates_path) if task_def.templates_path else None)
        raise RuntimeError(f"{task_def.entry} is not callable or class")

    def run_task(self, task_def: TaskDefinition) -> threading.Thread:
        log_store.log(f"Starting task {task_def.id}: {task_def.name}", task_id=task_def.id)
        task_instance = self._build_instance(task_def)

        def _runner():
            try:
                task_instance.ensure_window_focused()
                task_instance.run()
                log_store.log(f"Task {task_def.id} finished", task_id=task_def.id)
            except Exception as exc:  # pragma: no cover - runtime feedback
                log_store.log(f"Task {task_def.id} failed: {exc}", level="ERROR", task_id=task_def.id)

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        self._threads[task_def.id] = thread
        return thread


executor = TaskExecutor()
