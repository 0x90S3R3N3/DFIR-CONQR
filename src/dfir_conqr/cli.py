from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from dfir_conqr import __version__
from dfir_conqr.core import collectors as _collectors  # noqa: F401  (registers collectors)
from dfir_conqr.core.collector_base import all_collectors
from dfir_conqr.core.manifest import build_manifest, write_manifest
from dfir_conqr.core.report import write_html_report, write_json_report

console = Console()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="conqr-cli",
        description="Headless digital forensic triage collection (DFIR-CONQR)",
    )
    p.add_argument("--list", action="store_true", help="List available collectors and exit")
    p.add_argument("-o", "--output", type=Path, default=Path("./triage_output"), help="Output/case directory")
    p.add_argument("-c", "--collectors", nargs="*", help="Specific collector names to run (default: all)")
    p.add_argument("--case-id", default=None, help="Case identifier for the report/manifest")
    p.add_argument("--examiner", default=None, help="Examiner name for the report/manifest")
    p.add_argument("--version", action="version", version=f"DFIR-CONQR {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = all_collectors()

    if args.list:
        console.print("[bold]Available collectors:[/bold]")
        for name, cls in registry.items():
            console.print(f"  [cyan]{name}[/cyan] - {cls.description}")
        return 0

    selected = args.collectors if args.collectors else list(registry.keys())
    unknown = [c for c in selected if c not in registry]
    if unknown:
        console.print(f"[red]Unknown collector(s): {', '.join(unknown)}[/red]")
        return 1

    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Running triage collection...", total=len(selected))
        for name in selected:
            progress.update(task, description=f"Collecting: {name}")
            collector = registry[name]()
            result = collector.run(output_dir)
            results.append(result.to_dict())
            progress.advance(task)

    all_artifacts = [a for r in results for a in r.get("artifact_files", [])]
    manifest = build_manifest(
        case_id=args.case_id or "UNSET-CASE-ID",
        examiner=args.examiner or getpass.getuser(),
        output_dir=output_dir,
        artifact_relpaths=all_artifacts,
        tool_version=__version__,
    )
    write_manifest(manifest, output_dir)

    case_meta = {"case_id": args.case_id or "UNSET-CASE-ID", "examiner": args.examiner or getpass.getuser()}
    json_path = write_json_report(results, case_meta, output_dir)
    html_path = write_html_report(results, case_meta, output_dir)

    console.print(f"\n[green]Done.[/green] Report written to:\n  {json_path}\n  {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
