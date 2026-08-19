from __future__ import annotations

import platform
import socket
import time
from pathlib import Path
from typing import Any

import psutil

from dfir_conqr.core.collector_base import BaseCollector, register


@register
class SystemInfoCollector(BaseCollector):
    name = "system_info"
    description = "Hostname, OS version, boot time, timezone, disks, memory"

    def collect(self, output_dir: Path) -> tuple[dict[str, Any], list[str]]:
        boot_ts = psutil.boot_time()
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()

        disks = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_bytes": usage.total,
                        "used_bytes": usage.used,
                        "free_bytes": usage.free,
                    }
                )
            except (PermissionError, OSError):
                continue

        data = {
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "boot_time_epoch": boot_ts,
            "boot_time_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(boot_ts)),
            "collection_time_epoch": time.time(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "memory_total_bytes": vm.total,
            "memory_available_bytes": vm.available,
            "swap_total_bytes": sw.total,
            "disks": disks,
        }
        return data, []
