from __future__ import annotations

_DEBUG = False


def setup(debug: bool) -> None:
    global _DEBUG
    _DEBUG = debug


def info(msg: str) -> None:
    print(f"[INFO] {msg}")


def debug(msg: str) -> None:
    if _DEBUG:
        print(f"[DEBUG] {msg}")


def error(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr)
