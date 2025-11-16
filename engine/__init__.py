"""
Core engine exports for the desktop auto click framework.
"""

from .config import get_assets_dir, get_frontend_dir, get_scripts_dir, is_frozen
from .window import TargetWindowConfig

__all__ = [
    "TargetWindowConfig",
    "get_assets_dir",
    "get_frontend_dir",
    "get_scripts_dir",
    "is_frozen",
]
