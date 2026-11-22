"""Backward-compatible CLI entry point; the supported command is main.py."""

from main import main


if __name__ == "__main__":
    raise SystemExit(main())
