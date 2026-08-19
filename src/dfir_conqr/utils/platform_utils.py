from __future__ import annotations

import ctypes
import os
import platform


def current_os() -> str:
    return platform.system()


def is_elevated() -> bool:
    """Best-effort check for admin/root - some collectors need it for full data."""
    system = platform.system()
    try:
        if system == "Windows":
            return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
        return os.geteuid() == 0  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return False
