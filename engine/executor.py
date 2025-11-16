from __future__ import annotations

import importlib.util
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
        self._instances: Dict[str, TaskBase] = {}

    def _build_instance(self, task_def: TaskDefinition) -> TaskBase:
        module_path = Path(task_def.script)
        if not module_path.is_absolute():
            if task_def.path:
                module_path = Path(task_def.path) / module_path
            else:
                module_path = get_scripts_dir() / module_path
        log_store.log(f"[executor] load script: {module_path}", level="TEST", task_id=task_def.id)

        module_name = f"tasks.{task_def.id}"
        # 按文件路径加载，并用任务ID作模块名避免 main.py 同名冲突
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if not spec or not spec.loader:
            raise RuntimeError(f"无法加载任务脚本: {module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)  # type: ignore[arg-type]
        cls_or_func = getattr(module, task_def.entry)

        template_path = None
        if task_def.templates_path:
            template_path = Path(task_def.templates_path)
            if not template_path.is_absolute() and task_def.path:
                template_path = Path(task_def.path) / template_path
        elif task_def.path:
            # fallback to task folder default templates.yaml
            template_path = Path(task_def.path) / "templates.yaml"

        if isinstance(cls_or_func, type):
            return cls_or_func(
                target_window=task_def.target_window,
                template_config_path=template_path,
                task_id=task_def.id,
            )
        if isinstance(cls_or_func, Callable):
            class FuncTask(TaskBase):
                def run(self, context=None):
                    return cls_or_func(self, context=context)

            return FuncTask(
                target_window=task_def.target_window,
                template_config_path=template_path,
                task_id=task_def.id,
            )
        raise RuntimeError(f"{task_def.entry} is not callable or class")

    def run_task(self, task_def: TaskDefinition) -> threading.Thread:
        log_store.log(f"Starting task {task_def.id}: {task_def.name}", task_id=task_def.id)
        task_instance = self._build_instance(task_def)
        self._instances[task_def.id] = task_instance

        def _runner():
            try:
                if task_instance.target_window_config:
                    task_instance.ensure_window_focused()
                task_instance.run()
                log_store.log(f"Task {task_def.id} finished", task_id=task_def.id)
            except Exception as exc:  # pragma: no cover - runtime feedback
                log_store.log(f"Task {task_def.id} failed: {exc}", level="ERROR", task_id=task_def.id)

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        self._threads[task_def.id] = thread
        return thread

    def stop_task(self, task_id: str) -> bool:
        task = self._instances.get(task_id)
        if not task:
            return False
        task.request_stop()
        thread = self._threads.get(task_id)
        if thread and thread.is_alive():
            thread.join(timeout=1.0)
        return True


executor = TaskExecutor()
