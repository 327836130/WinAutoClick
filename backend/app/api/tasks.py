from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List
import yaml

from fastapi import APIRouter, HTTPException, Body

from engine import config as engine_config
from engine.executor import TaskDefinition, executor
from engine.window import TargetWindowConfig

from ..models.schemas import TaskDefinitionModel, TaskListResponse

router = APIRouter(prefix="/api/tasks")

TASKS_PATH = engine_config.get_assets_dir() / "tasks.json"


def _load_tasks() -> List[Dict]:
    if not TASKS_PATH.exists():
        TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
        TASKS_PATH.write_text("[]", encoding="utf-8")
        return []
    try:
        content = TASKS_PATH.read_bytes().decode("utf-8-sig")
        tasks = json.loads(content)
        dirty = False
        for t in tasks:
            tw = t.get("target_window") or {}
            if tw.get("hwnd"):
                tw["hwnd"] = None
                t["target_window"] = tw
                dirty = True
                # 同步更新 task.yaml 中的 target_window
                task_dir = Path(t.get("path") or engine_config.get_tasks_root() / t.get("id", ""))
                task_yaml = task_dir / "task.yaml"
                if task_yaml.exists():
                    try:
                        data = yaml.safe_load(task_yaml.read_text(encoding="utf-8")) or {}
                        data["target_window"] = tw
                        task_yaml.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
                    except Exception:
                        pass
        if dirty:
            TASKS_PATH.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
        return tasks
    except Exception:
        return []


def _write_tasks(tasks: List[Dict]) -> None:
    TASKS_PATH.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def _discover_tasks_from_disk() -> List[Dict]:
    """Scan tasks/ directory for task.yaml to enrich the list even if tasks.json is empty."""
    results: List[Dict] = []
    root = engine_config.get_tasks_root()
    if not root.exists():
        return results
    for sub in root.iterdir():
        if not sub.is_dir():
            continue
        task_yaml = sub / "task.yaml"
        if not task_yaml.exists():
            continue
        try:
            data = yaml.safe_load(task_yaml.read_text(encoding="utf-8")) or {}
            results.append(
                {
                    "id": data.get("id") or sub.name,
                    "name": data.get("name") or sub.name,
                    "script": data.get("script", "main.py"),
                    "entry": data.get("entry", "MainTask"),
                    "path": str(sub),
                    "templates_path": str(sub / data.get("templates", "templates.yaml")),
                    "target_window": data.get("target_window") or {},
                }
            )
        except Exception:
            continue
    return results


@router.get("/", response_model=TaskListResponse)
def list_tasks():
    tasks = _load_tasks()
    seen_ids = {t["id"] for t in tasks}
    # merge disk-discovered tasks
    for t in _discover_tasks_from_disk():
        if t["id"] not in seen_ids:
            tasks.append(t)
    enriched = []
    for t in tasks:
        task_dir = Path(t.get("path") or engine_config.get_tasks_root() / t["id"])
        task_yaml = task_dir / "task.yaml"
        merged = dict(t)
        if task_yaml.exists():
            try:
                data = yaml.safe_load(task_yaml.read_text(encoding="utf-8")) or {}
                merged.update(
                    {
                        "script": data.get("script", merged.get("script")),
                        "entry": data.get("entry", merged.get("entry")),
                        "templates_path": str((task_dir / data.get("templates", "templates.yaml")).as_posix()),
                        "target_window": data.get("target_window", merged.get("target_window")),
                    }
                )
            except Exception:
                pass
        enriched.append(merged)
    return {"tasks": enriched}


@router.post("/", response_model=TaskDefinitionModel)
def save_task(task: TaskDefinitionModel):
    try:
        tasks = _load_tasks()
        # upsert
        tasks = [t for t in tasks if t["id"] != task.id]

        # Ensure task directory
        task_dir = task.path or str(engine_config.get_tasks_root() / task.id)
        task_path = Path(task_dir)
        task_path.mkdir(parents=True, exist_ok=True)

        # Write task.yaml
        task_yaml = {
            "id": task.id,
            "name": task.name,
            "script": task.script or "main.py",
            "entry": task.entry or "MainTask",
            "templates": task.templates_path or "templates.yaml",
            "target_window": task.target_window.dict() if task.target_window else {},
        }
        (task_path / "task.yaml").write_text(yaml.safe_dump(task_yaml, allow_unicode=True), encoding="utf-8")
        # Ensure templates.yaml exists
        templates_file = task_path / (task.templates_path or "templates.yaml")
        if not templates_file.exists():
            templates_file.write_text("templates: {}\n", encoding="utf-8")
        # Ensure main script stub
        script_file = task_path / (task.script or "main.py")
        if not script_file.exists():
            default_content = (
                "from engine.task_base import TaskBase\n\n"
                "class MainTask(TaskBase):\n"
                "    def run(self, context=None):\n"
                "        self.log('hello from task')\n"
            )
            script_file.write_text(task.script_content or default_content, encoding="utf-8")
        else:
            # 如果传入了脚本文本则覆盖
            if task.script_content:
                script_file.write_text(task.script_content, encoding="utf-8")

        tasks.append(
            {
                "id": task.id,
                "name": task.name,
                "script": task.script or "main.py",
                "entry": task.entry or "MainTask",
                "path": str(task_path),
                "templates_path": str(templates_file),
                "target_window": task.target_window.dict() if task.target_window else {},
            }
        )
        _write_tasks(tasks)
        return TaskDefinitionModel(**tasks[-1])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"save_task error: {exc}") from exc


@router.post("/{task_id}/run")
def run_task(task_id: str):
    tasks = _load_tasks()
    target = next((t for t in tasks if t["id"] == task_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="任务不存在")
    # 必须预先绑定窗口
    if not target.get("target_window") or not target["target_window"].get("hwnd"):
        raise HTTPException(status_code=400, detail="请先在任务中绑定窗口（target_window.hwnd）再运行")

    task_dir = Path(target.get("path") or engine_config.get_tasks_root() / target["id"])
    task_yaml = task_dir / "task.yaml"
    script = target["script"]
    entry = target["entry"]
    templates_path = target.get("templates_path") or (task_dir / "templates.yaml")
    cfg = target.get("target_window") or {}
    if task_yaml.exists():
        data = yaml.safe_load(task_yaml.read_text(encoding="utf-8")) or {}
        script = data.get("script", script)
        entry = data.get("entry", entry)
        templates_path = task_dir / data.get("templates", "templates.yaml")
        cfg = data.get("target_window") or cfg
    task_def = TaskDefinition(
        id=target["id"],
        name=target["name"],
        script=str(task_dir / script),
        entry=entry,
        path=str(task_dir),
        templates_path=str(templates_path),
        target_window=TargetWindowConfig(
            title_contains=cfg.get("title_contains"), process_name=cfg.get("process_name"), hwnd=cfg.get("hwnd")
        ),
    )
    executor.run_task(task_def)
    return {"status": "started"}


@router.get("/{task_id}/script")
def get_task_script(task_id: str):
    tasks = _load_tasks()
    target = next((t for t in tasks if t["id"] == task_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="任务不存在")
    task_dir = Path(target.get("path") or engine_config.get_tasks_root() / task_id)
    task_yaml = task_dir / "task.yaml"
    script_name = target.get("script", "main.py")
    if task_yaml.exists():
        try:
            data = yaml.safe_load(task_yaml.read_text(encoding="utf-8")) or {}
            script_name = data.get("script", script_name)
        except Exception:
            pass
    script_path = task_dir / script_name
    if not script_path.exists():
        raise HTTPException(status_code=404, detail="脚本文件不存在")
    return {"content": script_path.read_text(encoding="utf-8")}


@router.post("/{task_id}/script")
def save_task_script(task_id: str, content: str = Body(..., embed=True)):
    tasks = _load_tasks()
    target = next((t for t in tasks if t["id"] == task_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="任务不存在")
    task_dir = Path(target.get("path") or engine_config.get_tasks_root() / task_id)
    task_yaml = task_dir / "task.yaml"
    script_name = target.get("script", "main.py")
    if task_yaml.exists():
        try:
            data = yaml.safe_load(task_yaml.read_text(encoding="utf-8")) or {}
            script_name = data.get("script", script_name)
        except Exception:
            pass
    script_path = task_dir / script_name
    script_path.write_text(content, encoding="utf-8")
    return {"status": "ok"}
