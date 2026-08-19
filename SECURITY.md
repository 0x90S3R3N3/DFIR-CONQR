# Security Policy

This tool is used in security/incident-response contexts, so we take vulnerability
reports seriously.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, use GitHub's private vulnerability reporting:
`Security` tab → `Report a vulnerability` on this repository.

If that isn't available, email the maintainer listed in `pyproject.toml` with:
- A description of the issue
- Steps to reproduce
- Potential impact (e.g. could it be used to tamper with evidence integrity,
  execute arbitrary code, or leak collected data)

We aim to acknowledge reports within 5 business days.

## Scope notes

- This tool reads and copies data from the host it runs on; it is explicitly
  designed to be read-only/non-destructive. Any collector that writes to or
  modifies the target system outside of its own output directory is considered
  a bug/vulnerability.
- Chain-of-custody hashes (`chain_of_custody.json`) are for integrity verification,
  not cryptographic non-repudiation - do not represent them to end users as
  legally signed evidence without an appropriate signing step.
