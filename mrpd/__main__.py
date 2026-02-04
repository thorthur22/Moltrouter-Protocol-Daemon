"""Allow `python -m mrpd ...` / `py -m mrpd ...` to run the CLI.

Windows users often have `mrpd.exe` installed but not on PATH.
Module execution is a reliable fallback.
"""

from __future__ import annotations

from mrpd.cli import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
