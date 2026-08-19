"""
Base class and registry for all triage collectors.

Every collector is a self-contained unit that:
  1. Declares a unique name/description/platform support
  2. Gathers volatile or on-disk artifacts
  3. Returns a structured, JSON-serializable result
  4. Optionally writes raw artifact files into the case output directory

Collectors must never raise uncaught exceptions - failures are captured
in the result so one failing module never aborts the whole triage run.
"""

from __future__ import annotations

import platform
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CollectorResult:
    name: str
    status: str  # "success" | "partial" | "error" | "skipped"
    started_at: float
    finished_at: float | None = None
    data: dict[str, Any] = field(default_factory=dict)
    artifact_files: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_seconds": (
                round(self.finished_at - self.started_at, 3) if self.finished_at else None
            ),
            "data": self.data,
            "artifact_files": self.artifact_files,
            "error": self.error,
        }


class BaseCollector(ABC):
    """Subclass this for every new triage module."""

    #: short unique identifier, e.g. "processes"
    name: str = "base"
    #: human readable description shown in the GUI
    description: str = ""
    #: which OSes this collector supports: any of "Windows", "Linux", "Darwin"
    supported_platforms: tuple[str, ...] = ("Windows", "Linux", "Darwin")

    def is_supported(self) -> bool:
        return platform.system() in self.supported_platforms

    def run(self, output_dir: Path) -> CollectorResult:
        """Wraps collect() with timing + exception safety. Do not override."""
        started = time.time()
        if not self.is_supported():
            return CollectorResult(
                name=self.name,
                status="skipped",
                started_at=started,
                finished_at=time.time(),
                error=f"Not supported on {platform.system()}",
            )
        try:
            data, artifacts = self.collect(output_dir)
            return CollectorResult(
                name=self.name,
                status="success",
                started_at=started,
                finished_at=time.time(),
                data=data,
                artifact_files=artifacts,
            )
        except Exception:  # noqa: BLE001 - intentional: isolate collector failures
            return CollectorResult(
                name=self.name,
                status="error",
                started_at=started,
                finished_at=time.time(),
                error=traceback.format_exc(),
            )

    @abstractmethod
    def collect(self, output_dir: Path) -> tuple[dict[str, Any], list[str]]:
        """
        Do the actual collection work.

        Returns:
            (data, artifact_file_paths)
            data: JSON-serializable dict of findings, embedded directly in the report
            artifact_file_paths: paths (relative to output_dir) of any raw files
                                  written to disk (e.g. copied browser DBs)
        """
        raise NotImplementedError


# --- Simple registry so the GUI/CLI can discover collectors dynamically ---

_REGISTRY: dict[str, type[BaseCollector]] = {}


def register(cls: type[BaseCollector]) -> type[BaseCollector]:
    """Class decorator: @register on every BaseCollector subclass."""
    _REGISTRY[cls.name] = cls
    return cls


def all_collectors() -> dict[str, type[BaseCollector]]:
    return dict(_REGISTRY)
