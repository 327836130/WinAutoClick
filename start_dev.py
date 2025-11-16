from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _base_dir() -> Path:
    # When frozen, the exe lives in dist/, need to go one level up to project root.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent.parent
    return Path(__file__).resolve().parent


ROOT = _base_dir()
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "ui"
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"


def _start_process(cmd, cwd: Path):
    # Spawn a process without blocking; hide window flag for powershell if needed.
    return subprocess.Popen(cmd, cwd=str(cwd))


def start_backend():
    py = VENV_PYTHON if VENV_PYTHON.exists() else sys.executable
    cmd = [
        str(py),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]
    return _start_process(cmd, BACKEND_DIR)


def start_frontend():
    npm_path = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm_path:
        raise FileNotFoundError("npm 未找到，请确认已安装 Node.js 并将 npm 加入 PATH")
    env = os.environ.copy()
    # 强制 npm 使用 cmd 作为脚本 shell，避免 PowerShell 执行策略限制
    env["NPM_CONFIG_SCRIPT_SHELL"] = r"C:\Windows\System32\cmd.exe"
    env["npm_config_script_shell"] = r"C:\Windows\System32\cmd.exe"
    cmd = [npm_path, "run", "dev", "--", "--host", "--port", "5173"]
    return subprocess.Popen(cmd, cwd=str(FRONTEND_DIR), env=env, shell=False)


def main():
    print("Starting backend (uvicorn)...")
    backend_proc = start_backend()
    time.sleep(2)
    print("Starting frontend (npm run dev)...")
    frontend_proc = start_frontend()

    def open_browser():
        time.sleep(3)
        try:
            webbrowser.open("http://127.0.0.1:5173")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("Backend exited.")
                break
            if frontend_proc.poll() is not None:
                print("Frontend exited.")
                break
    finally:
        for p in (backend_proc, frontend_proc):
            if p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass


if __name__ == "__main__":
    main()
