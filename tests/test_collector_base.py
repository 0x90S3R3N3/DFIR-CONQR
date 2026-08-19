from pathlib import Path

from dfir_conqr.core.collector_base import (
    BaseCollector,
    CollectorResult,
    all_collectors,
    register,
)


def test_failed_collector_is_isolated(tmp_path: Path):
    @register
    class _AlwaysFails(BaseCollector):
        name = "_test_always_fails"
        description = "test"

        def collect(self, output_dir: Path):
            raise RuntimeError("boom")

    result = _AlwaysFails().run(tmp_path)
    assert isinstance(result, CollectorResult)
    assert result.status == "error"
    assert "boom" in result.error


def test_registry_contains_builtin_collectors():
    import dfir_conqr.core.collectors  # noqa: F401

    registry = all_collectors()
    assert "system_info" in registry
    assert "processes" in registry


def test_skips_on_unsupported_platform(tmp_path: Path, monkeypatch):
    class _WindowsOnly(BaseCollector):
        name = "_test_windows_only"
        supported_platforms = ("Windows",)

        def collect(self, output_dir: Path):
            return {}, []

    monkeypatch.setattr("platform.system", lambda: "Linux")
    result = _WindowsOnly().run(tmp_path)
    assert result.status == "skipped"
