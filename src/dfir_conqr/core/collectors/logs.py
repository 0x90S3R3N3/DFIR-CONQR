"""
Pulls a recent window of system/security logs using the OS's native
log query tools. Writes the raw output to a text artifact file and
stores only a short preview + line count in the JSON report (logs can
be huge).
"""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from typing import Any

from dfir_conqr.core.collector_base import BaseCollector, register


def _run(cmd: list[str], timeout: int = 30) -> str:
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return (out.stdout or "") + (out.stderr or "")
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return f"<error running {cmd}: {e}>"


@register
class LogsCollector(BaseCollector):
    name = "logs"
    description = "Recent system/security event log entries (native OS tools)"

    LOOKBACK_LINES_PREVIEW = 50

    def collect(self, output_dir: Path) -> tuple[dict[str, Any], list[str]]:
        system = platform.system()
        artifacts: list[str] = []

        if system == "Windows":
            raw = _run(
                ["wevtutil", "qe", "System", "/c:200", "/rd:true", "/f:text"]
            )
            label = "windows_system_eventlog"
        elif system == "Linux":
            raw = _run(["journalctl", "-n", "500", "--no-pager"])
            label = "linux_journalctl"
        elif system == "Darwin":
            raw = _run(["log", "show", "--last", "1h", "--style", "syslog"])
            label = "macos_unified_log"
        else:
            return {"error": f"unsupported platform {system}"}, []

        out_path = output_dir / f"{label}.txt"
        out_path.write_text(raw, encoding="utf-8", errors="replace")
        artifacts.append(out_path.name)

        lines = raw.splitlines()
        data = {
            "source": label,
            "total_lines_captured": len(lines),
            "preview": lines[: self.LOOKBACK_LINES_PREVIEW],
            "full_log_artifact": out_path.name,
        }
        return data, artifacts
