# mrpd (npm wrapper)

This folder contains a small Node.js launcher for the **MRPd** Python CLI.

## Why
Some developers reach for `npx`/`npm -g` first. This wrapper aims to make:

```bash
npx mrpd ...
```

work, while keeping the **Python package** as the source of truth.

## How it works
- Requires Python 3.
- Creates a runtime venv at `~/.mrpd/runtime/venv`.
- Installs the PyPI package (default: `mrpd`) into that venv.
- Runs: `python -m mrpd.cli <args>`

## Dev mode (monorepo)
If you are working inside the `mrpd` repo, you can run the repo version directly:

```bash
MRPD_USE_REPO=1 npx ./npm/bin/mrpd.js version
```

## Env overrides
- `MRPD_PYPI_PACKAGE` (default: `mrpd`)
- `MRPD_PYPI_VERSION` (optional, e.g. `0.1.0`)
