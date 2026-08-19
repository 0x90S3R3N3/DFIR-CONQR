from __future__ import annotations

from pathlib import Path
from typing import Any

import psutil

from dfir_conqr.core.collector_base import BaseCollector, register


@register
class NetworkCollector(BaseCollector):
    name = "network"
    description = "Network interfaces, addresses, and active connections"

    def collect(self, output_dir: Path) -> tuple[dict[str, Any], list[str]]:
        interfaces = {}
        for iface, addrs in psutil.net_if_addrs().items():
            interfaces[iface] = [
                {"family": str(a.family), "address": a.address, "netmask": a.netmask}
                for a in addrs
            ]

        stats = {
            iface: {"is_up": s.isup, "speed_mbps": s.speed, "mtu": s.mtu}
            for iface, s in psutil.net_if_stats().items()
        }

        connections = []
        try:
            for c in psutil.net_connections(kind="inet"):
                connections.append(
                    {
                        "fd": c.fd,
                        "family": str(c.family),
                        "type": str(c.type),
                        "local_addr": f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else None,
                        "remote_addr": f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else None,
                        "status": c.status,
                        "pid": c.pid,
                    }
                )
        except (psutil.AccessDenied, PermissionError):
            # Common on macOS/Linux without elevated privileges
            pass

        data = {
            "interfaces": interfaces,
            "interface_stats": stats,
            "connection_count": len(connections),
            "connections": connections,
        }
        return data, []
