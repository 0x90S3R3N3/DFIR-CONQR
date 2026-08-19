import hashlib
from pathlib import Path

from dfir_conqr.core.manifest import build_manifest, sha256_file


def test_sha256_file_matches_known_hash(tmp_path: Path):
    f = tmp_path / "sample.txt"
    f.write_text("hello world")
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert sha256_file(f) == expected


def test_build_manifest_includes_artifact_hashes(tmp_path: Path):
    f = tmp_path / "artifact.txt"
    f.write_text("evidence")
    manifest = build_manifest(
        case_id="CASE-1",
        examiner="tester",
        output_dir=tmp_path,
        artifact_relpaths=["artifact.txt"],
        tool_version="0.1.0",
    )
    assert manifest["case_id"] == "CASE-1"
    assert len(manifest["artifacts"]) == 1
    assert manifest["artifacts"][0]["path"] == "artifact.txt"
    assert len(manifest["artifacts"][0]["sha256"]) == 64
