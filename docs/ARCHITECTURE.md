# Architecture

```
dfir_conqr/
├── cli.py                 # headless entry point (conqr-cli)
├── gui/
│   ├── app.py              # GUI entry point (conqr-gui)
│   └── main_window.py      # PySide6 window; runs collection on a QThread
└── core/
    ├── collector_base.py   # BaseCollector, CollectorResult, registry
    ├── manifest.py         # SHA-256 hashing + chain-of-custody JSON
    ├── report.py           # JSON + HTML report writers
    └── collectors/         # one module per artifact type
        ├── system_info.py
        ├── processes.py
        ├── network.py
        ├── users_sessions.py
        ├── autoruns_persistence.py
        ├── logs.py
        ├── filesystem_artifacts.py
        └── browser_artifacts.py
```

## Design principles

1. **GUI and CLI are thin wrappers around `core`.** Neither contains collection
   logic itself - they just discover collectors via the registry, run them, and
   render/report the results. This means every collector automatically works in
   both interfaces, and a future third interface (e.g. a REST API) is cheap to add.

2. **Collectors are isolated and fail-soft.** `BaseCollector.run()` wraps every
   collector's `collect()` in a try/except. A traceback in one module becomes a
   `status: "error"` entry in the report, not a crashed triage run. This matters
   a lot in IR - you often only get one shot at a live host.

3. **Collectors declare their own platform support.** `supported_platforms` on
   the class lets the base `run()` auto-skip modules on the wrong OS rather than
   scattering `if platform.system() == ...` checks throughout the GUI/CLI.

4. **Everything written to disk is hashed.** Any artifact file a collector writes
   (browser DB copies, raw log dumps) must be returned in the `artifact_relpaths`
   list from `collect()`. The CLI/GUI then hash every one of those into
   `chain_of_custody.json` automatically - you don't have to remember to do it
   per collector.

5. **Read-only by design.** No collector should ever write outside of the
   provided `output_dir`, modify the registry/filesystem it's inspecting, or
   require destructive elevation tricks. This keeps the tool safe to run on a
   live, in-scope host during an active investigation.

## Adding a new collector

See [`CONTRIBUTING.md`](../CONTRIBUTING.md#adding-a-new-collector).

## Why not parse everything (e.g. SQLite browser history) in-process?

Triage is about speed and safety on a live system. Parsing formats like SQLite,
registry hives, or Prefetch is often better done **offline**, against the copied
artifact, using dedicated parsing libraries (e.g. `python-registry`, `dissect`,
`evtx`) - so a bug in a parser can't crash collection or hang on a locked file.
The roadmap includes an optional offline-parsing pass; today collectors that
touch these formats focus on locating and safely copying them.
