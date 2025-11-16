from __future__ import annotations

import threading
import webbrowser

import uvicorn

from app.main import app


def _open_browser():
    try:
        webbrowser.open_new_tab("http://127.0.0.1:8000")
    except Exception:
        pass


def main():
    threading.Timer(1.0, _open_browser).start()
    print("服务已启动，请打开 http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
