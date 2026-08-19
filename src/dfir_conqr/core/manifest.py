"""
Chain-of-custody support: hash every artifact file we write, and
produce a signed-looking manifest (examiner, machine, timestamps, hashes)
so the collection can be verified/attested later.
"""

from __future__ import annotations

import getpass
import hashlib
import json
import platform
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(
    case_id: str,
    examiner: str,
    output_dir: Path,
    artifact_relpaths: list[str],
    tool_version: str,
) -> dict[str, Any]:
    entries = []
    for rel in artifact_relpaths:
        full = output_dir / rel
        if full.exists() and full.is_file():
            entries.append(
                {
                    "path": rel,
                    "size_bytes": full.stat().st_size,
                    "sha256": sha256_file(full),
                }
            )
    return {
        "case_id": case_id,
        "examiner": examiner,
        "tool": "DFIR-CONQR",
        "tool_version": tool_version,
        "collection_started_utc": datetime.now(timezone.utc).isoformat(),
        "collecting_host": {
            "hostname": socket.gethostname(),
            "os": platform.platform(),
            "operator_account": getpass.getuser(),
        },
        "artifacts": entries,
    }


def write_manifest(manifest: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "chain_of_custody.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path
