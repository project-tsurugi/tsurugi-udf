from __future__ import annotations

import os
import sys
from collections.abc import Iterable

_DEBUG = False

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code: str, msg: str) -> str:
    if not _USE_COLOR:
        return msg
    return f"\033[{code}m{msg}\033[0m"


def setup(debug: bool, *, color: bool | None = None) -> None:
    global _DEBUG, _USE_COLOR
    _DEBUG = debug
    if color is not None:
        _USE_COLOR = color and sys.stdout.isatty()


def info(msg: str, *, end: str = "\n") -> None:
    prefix = _c("1;34", "[INFO] ")
    print(prefix + msg, end=end)


def debug(msg: str, *, end: str = "\n") -> None:
    if not _DEBUG:
        return
    prefix = _c("2;37", "[DEBUG] ")
    print(prefix + msg, end=end)


def debug_list(title: str, items: Iterable[object]) -> None:
    if not _DEBUG:
        return
    items_list = list(items)
    prefix = _c("2;37", "[DEBUG] ")
    print(prefix + f"{title}: {len(items_list)}")
    for x in items_list:
        print(prefix + f"  - {x}")


def error(msg: str, file=sys.stderr, end: str = "\n") -> None:
    prefix = _c("1;31", "[ERROR] ")
    print(prefix + msg, file=file, end=end)
