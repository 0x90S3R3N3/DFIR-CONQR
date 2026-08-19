"""
Enumerates common persistence locations per OS. This only *reads and lists*
existing configuration - it never modifies anything on the target system.

Windows : Run/RunOnce registry keys, scheduled tasks
Linux   : systemd user+system units, cron tables
macOS   : LaunchAgents/LaunchDaemons, cron
"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Any

from dfir_conqr.core.collector_base import BaseCollector, register


def _run(cmd: list[str], timeout: int = 15) -> str:
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return (out.stdout or "") + (out.stderr or "")
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return f"<error running {cmd}: {e}>"


@register
class PersistenceCollector(BaseCollector):
    name = "persistence"
    description = "Autostart/persistence locations: registry run keys, cron, systemd, launchd"

    def collect(self, output_dir: Path) -> tuple[dict[str, Any], list[str]]:
        system = platform.system()
        data: dict[str, Any] = {"platform": system}

        if system == "Windows":
            data["run_keys"] = self._windows_run_keys()
            data["scheduled_tasks_raw"] = _run(["schtasks", "/query", "/fo", "LIST", "/v"])

        elif system == "Linux":
            data["systemd_enabled_units"] = _run(
                ["systemctl", "list-unit-files", "--state=enabled", "--no-pager"]
            )
            data["crontab_current_user"] = _run(["crontab", "-l"])
            data["cron_d_listing"] = self._list_dir("/etc/cron.d")
            data["cron_daily_listing"] = self._list_dir("/etc/cron.daily")

        elif system == "Darwin":
            data["launch_agents_user"] = self._list_dir(
                os.path.expanduser("~/Library/LaunchAgents")
            )
            data["launch_agents_system"] = self._list_dir("/Library/LaunchAgents")
            data["launch_daemons_system"] = self._list_dir("/Library/LaunchDaemons")
            data["crontab_current_user"] = _run(["crontab", "-l"])

        return data, []

    @staticmethod
    def _list_dir(path: str) -> list[str]:
        try:
            return sorted(os.listdir(path))
        except (FileNotFoundError, PermissionError, NotADirectoryError):
            return []

    @staticmethod
    def _windows_run_keys() -> dict[str, Any]:
        results: dict[str, Any] = {}
        try:
            import winreg  # type: ignore

            hives = {
                "HKCU\\...\\Run": (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                "HKLM\\...\\Run": (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                "HKLM\\...\\RunOnce": (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            }
            for label, (hive, subkey) in hives.items():
                entries = {}
                try:
                    with winreg.OpenKey(hive, subkey) as key:
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                entries[name] = value
                                i += 1
                            except OSError:
                                break
                except FileNotFoundError:
                    pass
                results[label] = entries
        except ImportError:
            results["error"] = "winreg unavailable"
        return results
