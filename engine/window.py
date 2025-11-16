from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import psutil

try:
    import win32con
    import win32gui
    import win32process
except ImportError as exc:  # pragma: no cover - runtime platform guard
    raise RuntimeError("win32 APIs are required on Windows for window management") from exc


Rect = Tuple[int, int, int, int]


@dataclass
class TargetWindowConfig:
    title_contains: Optional[str] = None
    process_name: Optional[str] = None
    hwnd: Optional[int] = None


def _get_process_name(hwnd: int) -> str:
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name()
    except Exception:
        return ""


def _normalize_title(text: str) -> str:
    return text or ""


def list_windows() -> List[Dict]:
    windows: List[Dict] = []

    def _enum_handler(hwnd: int, _: int) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
        rect = win32gui.GetWindowRect(hwnd)
        windows.append(
            {
                "hwnd": hwnd,
                "title": title,
                "process_name": _get_process_name(hwnd),
                "rect": {"left": rect[0], "top": rect[1], "right": rect[2], "bottom": rect[3]},
            }
        )

    win32gui.EnumWindows(_enum_handler, 0)
    return windows


def find_window(config: TargetWindowConfig) -> Optional[int]:
    def _match(hwnd: int) -> bool:
        title = _normalize_title(win32gui.GetWindowText(hwnd))
        if config.title_contains and config.title_contains.lower() not in title.lower():
            return False
        if config.process_name:
            return _get_process_name(hwnd).lower() == config.process_name.lower()
        return True

    if config.hwnd:
        return config.hwnd if win32gui.IsWindow(config.hwnd) else None

    for info in list_windows():
        if _match(info["hwnd"]):
            return info["hwnd"]
    return None


def activate_window(hwnd: int) -> None:
    """
    Bring window to foreground without changing size.
    Only call SetForegroundWindow; preserve current window state (normal/最大化/最小化).
    """
    try:
        placement = win32gui.GetWindowPlacement(hwnd)
        show_cmd = placement[1]  # 1: normal, 2: minimized, 3: maximized
        # 如果最小化，保持最小化状态，不做前置以免还原尺寸
        if show_cmd == win32con.SW_SHOWMINIMIZED:
            return
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        # 前置后重新应用原 show_cmd（如最大化保持最大化）
        if show_cmd == win32con.SW_SHOWMAXIMIZED:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
        elif show_cmd == win32con.SW_SHOWNORMAL:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
    except Exception:
        pass


def get_window_rect(hwnd: int) -> Rect:
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return left, top, right, bottom


def window_exists(hwnd: int) -> bool:
    return win32gui.IsWindow(hwnd)


def map_window_to_screen(
    point: Tuple[int, int], rect_provider: Callable[[], Rect]
) -> Tuple[int, int]:
    left, top, right, bottom = rect_provider()
    x, y = point
    return left + x, top + y
