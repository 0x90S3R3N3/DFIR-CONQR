from __future__ import annotations

from pathlib import Path
from typing import Any

import psutil

from dfir_conqr.core.collector_base import BaseCollector, register


@register
class UsersSessionsCollector(BaseCollector):
    name = "users_sessions"
    description = "Currently logged-in users and their session origin"

    def collect(self, output_dir: Path) -> tuple[dict[str, Any], list[str]]:
        sessions = [
            {
                "username": u.name,
                "terminal": u.terminal,
                "host": u.host,
                "login_time_epoch": u.started,
                "pid": getattr(u, "pid", None),
            }
            for u in psutil.users()
        ]
        return {"session_count": len(sessions), "sessions": sessions}, []
