"""
Lists recently modified files in common "interesting" locations
(Downloads, Temp, Desktop, Startup folders) without copying full
content by default - triage is about pointing an investigator at
where to look next, not exfiltrating an entire disk.
"""

from __future__ import annotations

import os
import platform
import time
from pathlib import Path
from typing import Any

from dfir_conqr.core.collector_base import BaseCollector, register

MAX_FILES_PER_DIR = 200
RECENT_DAYS = 14


def _candidate_dirs() -> list[Path]:
    home = Path.home()
    system = platform.system()
    dirs = [home / "Downloads", home / "Desktop"]
    if system == "Windows":
        dirs += [
            Path(os.environ.get("TEMP", "")),
            home / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup",
        ]
    elif system == "Darwin":
        dirs += [Path("/tmp"), home / "Library/LaunchAgents"]
    else:  # Linux
        dirs += [Path("/tmp"), home / ".config/autostart"]
    return [d for d in dirs if d and d.exists()]


@register
class FilesystemArtifactsCollector(BaseCollector):
    name = "filesystem_artifacts"
    description = "Recently modified files in common staging/startup directories"

    def collect(self, output_dir: Path) -> tuple[dict[str, Any], list[str]]:
        cutoff = time.time() - RECENT_DAYS * 86400
        results: dict[str, Any] = {}

        for d in _candidate_dirs():
            entries = []
            try:
                with os.scandir(d) as it:
                    for entry in it:
                        try:
                            st = entry.stat(follow_symlinks=False)
                        except OSError:
                            continue
                        if st.st_mtime >= cutoff:
                            entries.append(
                                {
                                    "path": entry.path,
                                    "size_bytes": st.st_size,
                                    "mtime_epoch": st.st_mtime,
                                    "is_dir": entry.is_dir(follow_symlinks=False),
                                }
                            )
                        if len(entries) >= MAX_FILES_PER_DIR:
                            break
            except (PermissionError, FileNotFoundError):
                continue
            entries.sort(key=lambda e: e["mtime_epoch"], reverse=True)
            results[str(d)] = entries

        return {"lookback_days": RECENT_DAYS, "directories": results}, []
