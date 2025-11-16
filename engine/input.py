from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Tuple

import pyautogui

from .window import Rect, map_window_to_screen

pyautogui.FAILSAFE = False


@dataclass
class ClickPadding:
    left: float = 0
    right: float = 0
    top: float = 0
    bottom: float = 0


def _apply_padding(rect: Tuple[int, int, int, int], padding: ClickPadding) -> Tuple[int, int, int, int]:
    x, y, w, h = rect
    new_x = x + int(w * padding.left)
    new_y = y + int(h * padding.top)
    new_w = w - int(w * padding.left) - int(w * padding.right)
    new_h = h - int(h * padding.top) - int(h * padding.bottom)
    return new_x, new_y, max(1, new_w), max(1, new_h)


def pick_point(rect: Tuple[int, int, int, int], mode: str = "center", padding: ClickPadding | None = None) -> Tuple[int, int]:
    padding = padding or ClickPadding()
    rect = _apply_padding(rect, padding)
    x, y, w, h = rect
    if mode == "random":
        return x + random.randint(0, max(0, w - 1)), y + random.randint(0, max(0, h - 1))
    return x + w // 2, y + h // 2


def click_screen(point: Tuple[int, int], button: str = "left", clicks: int = 1, interval: float = 0.15) -> None:
    pyautogui.click(x=point[0], y=point[1], button=button, clicks=clicks, interval=interval)


def drag_screen(start: Tuple[int, int], end: Tuple[int, int], duration: float = 0.3) -> None:
    pyautogui.moveTo(start[0], start[1])
    pyautogui.dragTo(end[0], end[1], duration=duration, button="left")


def type_text(text: str, interval: float = 0.02) -> None:
    pyautogui.write(text, interval=interval)


def hotkey(*keys: str, interval: float = 0.02) -> None:
    pyautogui.hotkey(*keys, interval=interval)


class InputController:
    def __init__(self, rect_provider):
        self._rect_provider = rect_provider

    def to_screen(self, window_point: Tuple[int, int]) -> Tuple[int, int]:
        return map_window_to_screen(window_point, self._rect_provider)

    def click_rect(
        self,
        rect: Tuple[int, int, int, int],
        mode: str = "center",
        padding: ClickPadding | None = None,
        button: str = "left",
        clicks: int = 1,
        interval: float = 0.2,
    ) -> Tuple[int, int]:
        point = pick_point(rect, mode=mode, padding=padding)
        screen_point = self.to_screen(point)
        click_screen(screen_point, button=button, clicks=clicks, interval=interval)
        time.sleep(interval)
        return screen_point

    def click_point(self, point: Tuple[int, int], button: str = "left", clicks: int = 1, interval: float = 0.2) -> Tuple[int, int]:
        screen_point = self.to_screen(point)
        click_screen(screen_point, button=button, clicks=clicks, interval=interval)
        time.sleep(interval)
        return screen_point
