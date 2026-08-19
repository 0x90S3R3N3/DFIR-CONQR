# Contributing

Thanks for considering a contribution!

## Setting up a dev environment

```bash
git clone https://github.com/<your-username>/DFIR-CONQR.git
cd DFIR-CONQR
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

## Adding a new collector

1. Create `src/dfir_conqr/core/collectors/<your_module>.py`.
2. Subclass `BaseCollector`, set `name`, `description`, and optionally `supported_platforms`.
3. Implement `collect(self, output_dir: Path) -> tuple[dict, list[str]]`.
   - Return `(data, artifact_relpaths)`.
   - Never raise silently caught exceptions on purpose - let the base class's exception
     isolation handle failures. Do not crash the whole run.
   - If you write raw files to disk, put them under `output_dir` and return their
     relative paths so they get hashed into the chain-of-custody manifest.
4. Register it with the `@register` decorator and import it in
   `core/collectors/__init__.py`.
5. Add a test in `tests/`.
6. Run `ruff check src tests` and `pytest tests/` before opening a PR.

## Code style

- `ruff` for linting (config in `pyproject.toml`)
- Type hints encouraged on public functions
- Keep collectors read-only / non-destructive - this tool must never modify the
  system it's triaging

## Reporting bugs / requesting features

Use the GitHub issue templates. Please redact any real case data from logs/screenshots.

## Security issues

See [`SECURITY.md`](SECURITY.md) — do not open a public issue for a security vulnerability.
