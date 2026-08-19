# DFIR-CONQR

An open-source, cross-platform GUI + CLI tool for **digital forensic triage and incident response**.
It collects volatile and on-disk artifacts from a live Windows, Linux, or macOS host, hashes
everything for chain of custody, and produces a JSON + HTML report — in minutes, without a full
disk image.

> ⚠️ **For authorized use only.** This tool is intended for incident responders, forensic
> examiners, and security researchers operating with proper authorization on systems they own
> or are contracted to investigate. Running it against systems you don't have permission to
> access may be illegal in your jurisdiction.

## Features

- **GUI and CLI** from the same collection engine — use the GUI for interactive triage, the CLI
  for scripted/remote collection (e.g. over SSH or an RMM tool with no display).
- **Modular collectors** — each artifact type (processes, network state, persistence, logs,
  browser history, etc.) is an independent, sandboxed module. One failing collector never aborts
  the run.
- **Chain of custody** — every collected file is SHA-256 hashed into a `chain_of_custody.json`
  manifest alongside examiner/host metadata.
- **Cross-platform** — Windows, Linux, and macOS collectors share a common interface; platform-
  specific logic (registry, systemd, launchd) is isolated per module.
- **Human-readable report** — a self-contained HTML report plus machine-readable JSON for
  pipeline integration.

## Current collectors

| Name | Description | Platforms |
|---|---|---|
| `system_info` | Hostname, OS version, boot time, disks, memory | all |
| `processes` | Full process list: PID, PPID, owner, path, cmdline | all |
| `network` | Interfaces, addresses, active connections | all |
| `users_sessions` | Currently logged-in users/sessions | all |
| `persistence` | Autorun locations: registry Run keys, cron, systemd, launchd | all |
| `logs` | Recent system/security event log entries | all |
| `filesystem_artifacts` | Recently modified files in common staging/startup dirs | all |
| `browser_artifacts` | Locates + preserves Chrome/Edge/Firefox history & cookie DBs | all |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how to add a new collector.

## Installation

```bash
git clone https://github.com/<your-username>/DFIR-CONQR.git
cd DFIR-CONQR
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

### GUI

```bash
conqr-gui
```

Pick which collectors to run, choose an output/case directory, fill in case ID and examiner
name, and click **Start Triage Collection**. When finished, click **Open HTML Report**.

### CLI (headless)

```bash
# List available collectors
conqr-cli --list

# Run everything
conqr-cli -o ./case001 --case-id IR-2026-001 --examiner "J. Doe"

# Run specific collectors only
conqr-cli -o ./case001 -c system_info processes network persistence
```

Output directory will contain:
```
case001/
├── triage_report.json
├── triage_report.html
├── chain_of_custody.json
├── windows_system_eventlog.txt      # (or linux_journalctl.txt / macos_unified_log.txt)
└── browser_artifacts/
    └── Chrome/History
```

## Building a standalone executable

```bash
pip install pyinstaller
pyinstaller --name dfir-conqr --onefile --windowed -p src src/dfir_conqr/gui/app.py
```

## Roadmap

- [ ] Memory acquisition integration (winpmem / avml pointers, not bundled)
- [ ] Prefetch / Amcache / Shimcache parsing (Windows)
- [ ] YARA scanning pass over collected artifacts
- [ ] Timeline view in the GUI (super-timeline style)
- [ ] Signed/exportable PDF report
- [ ] Plugin system for community-contributed collectors

Contributions welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).
