from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image


@dataclass
class MatchResult:
    rect: Tuple[int, int, int, int]
    confidence: float


METHODS = {
    "TM_CCOEFF_NORMED": cv2.TM_CCOEFF_NORMED,
    "TM_CCORR_NORMED": cv2.TM_CCORR_NORMED,
    "TM_SQDIFF_NORMED": cv2.TM_SQDIFF_NORMED,
}


def _to_gray(image: Image.Image | np.ndarray) -> np.ndarray:
    if isinstance(image, Image.Image):
        image = np.array(image)
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return image


def match_template(
    image: Image.Image | np.ndarray,
    template: Image.Image | np.ndarray,
    threshold: float = 0.8,
    region: Optional[Tuple[int, int, int, int]] = None,
    method: str = "TM_CCOEFF_NORMED",
) -> Optional[MatchResult]:
    source_arr = _to_gray(image)
    template_arr = _to_gray(template)

    search_area = source_arr
    offset_x = 0
    offset_y = 0
    if region:
        x, y, w, h = region
        offset_x, offset_y = x, y
        search_area = source_arr[y : y + h, x : x + w]

    cv_method = METHODS.get(method, cv2.TM_CCOEFF_NORMED)
    res = cv2.matchTemplate(search_area, template_arr, cv_method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # For SQDIFF smaller is better; normalize logic for clarity.
    if cv_method in (cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED):
        best_val = 1 - min_val
        best_loc = min_loc
    else:
        best_val = max_val
        best_loc = max_loc

    if best_val < threshold:
        return None

    top_left = (best_loc[0] + offset_x, best_loc[1] + offset_y)
    h, w = template_arr.shape[:2]
    rect = (top_left[0], top_left[1], w, h)
    return MatchResult(rect=rect, confidence=float(best_val))
