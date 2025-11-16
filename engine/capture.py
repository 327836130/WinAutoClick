from __future__ import annotations

from typing import Tuple

import numpy as np
from PIL import Image, ImageGrab

from .window import Rect, get_window_rect


def capture_window(hwnd: int) -> Image.Image:
    rect = get_window_rect(hwnd)
    left, top, right, bottom = rect
    return ImageGrab.grab(bbox=(left, top, right, bottom))


def capture_window_array(hwnd: int) -> Tuple[Image.Image, np.ndarray]:
    image = capture_window(hwnd)
    return image, np.array(image)
