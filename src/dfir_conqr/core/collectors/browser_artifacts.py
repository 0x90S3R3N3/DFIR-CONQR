"""
Locates browser profile directories for Chrome/Edge/Firefox and copies
the small SQLite artifact files (History, Cookies metadata) into the
case output directory for later offline parsing. We copy rather than
parse in place because the browser may hold a lock on the live file.
"""

from __future__ import annotations

import platform
import shutil
from pathlib import Path
from typing import Any

from dfir_conqr.core.collector_base import BaseCollector, register

# Files worth preserving per Chromium-based profile
CHROMIUM_FILES = ["History", "Cookies", "Login Data", "Web Data"]
FIREFOX_FILES = ["places.sqlite", "cookies.sqlite", "logins.json"]


def _chromium_profile_roots() -> dict[str, Path]:
    home = Path.home()
    system = platform.system()
    roots = {}
    if system == "Windows":
        base = home / "AppData/Local"
        roots["Chrome"] = base / "Google/Chrome/User Data/Default"
        roots["Edge"] = base / "Microsoft/Edge/User Data/Default"
    elif system == "Darwin":
        base = home / "Library/Application Support"
        roots["Chrome"] = base / "Google/Chrome/Default"
        roots["Edge"] = base / "Microsoft Edge/Default"
    else:  # Linux
        base = home / ".config"
        roots["Chrome"] = base / "google-chrome/Default"
        roots["Edge"] = base / "microsoft-edge/Default"
    return roots


def _firefox_profile_dirs() -> list[Path]:
    home = Path.home()
    system = platform.system()
    if system == "Windows":
        base = home / "AppData/Roaming/Mozilla/Firefox/Profiles"
    elif system == "Darwin":
        base = home / "Library/Application Support/Firefox/Profiles"
    else:
        base = home / ".mozilla/firefox"
    if not base.exists():
        return []
    return [p for p in base.iterdir() if p.is_dir()]


@register
class BrowserArtifactsCollector(BaseCollector):
    name = "browser_artifacts"
    description = "Locates and preserves browser history/cookie DBs (Chrome, Edge, Firefox)"

    def collect(self, output_dir: Path) -> tuple[dict[str, Any], list[str]]:
        artifacts: list[str] = []
        found: dict[str, Any] = {}
        dest_root = output_dir / "browser_artifacts"

        for browser, profile_dir in _chromium_profile_roots().items():
            if not profile_dir.exists():
                continue
            copied = []
            for fname in CHROMIUM_FILES:
                src = profile_dir / fname
                if src.exists():
                    dest_dir = dest_root / browser
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    dest = dest_dir / fname
                    try:
                        shutil.copy2(src, dest)
                        rel = str(dest.relative_to(output_dir))
                        copied.append(rel)
                        artifacts.append(rel)
                    except (PermissionError, OSError) as e:
                        copied.append(f"<failed: {fname}: {e}>")
            if copied:
                found[browser] = {"profile_path": str(profile_dir), "copied_files": copied}

        firefox_profiles = _firefox_profile_dirs()
        if firefox_profiles:
            ff_entries = []
            for prof in firefox_profiles:
                copied = []
                for fname in FIREFOX_FILES:
                    src = prof / fname
                    if src.exists():
                        dest_dir = dest_root / "Firefox" / prof.name
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dest = dest_dir / fname
                        try:
                            shutil.copy2(src, dest)
                            rel = str(dest.relative_to(output_dir))
                            copied.append(rel)
                            artifacts.append(rel)
                        except (PermissionError, OSError) as e:
                            copied.append(f"<failed: {fname}: {e}>")
                if copied:
                    ff_entries.append({"profile_path": str(prof), "copied_files": copied})
            if ff_entries:
                found["Firefox"] = ff_entries

        return {"browsers_found": list(found.keys()), "details": found}, artifacts
