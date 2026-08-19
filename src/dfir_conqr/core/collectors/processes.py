from __future__ import annotations

from pathlib import Path
from typing import Any

import psutil

from dfir_conqr.core.collector_base import BaseCollector, register

_ATTRS = [
    "pid", "ppid", "name", "exe", "cmdline", "username",
    "create_time", "status", "cwd", "num_threads",
]


@register
class ProcessesCollector(BaseCollector):
    name = "processes"
    description = "Snapshot of all running processes with owner, path, and command line"

    def collect(self, output_dir: Path) -> tuple[dict[str, Any], list[str]]:
        procs: list[dict[str, Any]] = []
        errors = 0
        for p in psutil.process_iter(_ATTRS):
            try:
                info = p.info
                procs.append(
                    {
                        "pid": info.get("pid"),
                        "ppid": info.get("ppid"),
                        "name": info.get("name"),
                        "exe": info.get("exe"),
                        "cmdline": info.get("cmdline"),
                        "username": info.get("username"),
                        "create_time": info.get("create_time"),
                        "status": info.get("status"),
                        "cwd": info.get("cwd"),
                        "num_threads": info.get("num_threads"),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                errors += 1
                continue

        data = {
            "process_count": len(procs),
            "unreadable_process_count": errors,
            "processes": procs,
        }
        return data, []
