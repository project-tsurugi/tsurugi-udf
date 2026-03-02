from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import Any

_DEBUG = False
_INDENT = 0

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code: str, msg: str) -> str:
    if not _USE_COLOR:
        return msg
    return f"\033[{code}m{msg}\033[0m"


def setup(debug: bool, *, color: bool | None = None) -> None:
    global _DEBUG, _USE_COLOR
    _DEBUG = debug
    if color is not None:
        _USE_COLOR = bool(color) and sys.stdout.isatty()


def _indent_str() -> str:
    return "  " * _INDENT


def _fmt(obj: Any) -> str:
    if isinstance(obj, Path):
        s = str(obj)
    else:
        s = str(obj)

    try:
        home = str(Path.home())
        if s.startswith(home + os.sep):
            s = "~" + s[len(home) :]
    except Exception:
        pass

    return s


def _emit(prefix: str, msg: str, *, end: str = "\n", file=sys.stdout) -> None:
    print(prefix + _indent_str() + msg, end=end, file=file)


def info(msg: str, *, end: str = "\n") -> None:
    prefix = _c("1;34", "[INFO] ")
    _emit(prefix, msg, end=end)


def debug(msg: str, *, end: str = "\n") -> None:
    if not _DEBUG:
        return
    prefix = _c("2;37", "[DEBUG] ")
    _emit(prefix, msg, end=end)


def warn(msg: str, *, end: str = "\n") -> None:
    prefix = _c("1;33", "[WARN] ")
    _emit(prefix, msg, end=end)


def error(msg: str, *, end: str = "\n") -> None:
    prefix = _c("1;31", "[ERROR] ")
    _emit(prefix, msg, end=end, file=sys.stderr)


@contextmanager
def section(title: str, *, level: str = "INFO") -> Iterable[None]:
    global _INDENT
    if level.upper() == "DEBUG":
        debug(f"== {title} ==")
    else:
        info(f"== {title} ==")

    _INDENT += 1
    try:
        yield
    finally:
        _INDENT -= 1


def debug_list(
    title: str,
    items: Iterable[object],
    *,
    empty_note: str = "empty",
) -> None:
    if not _DEBUG:
        return

    items_list = list(items)
    n = len(items_list)

    if n == 0:
        debug(f"{title}: 0 ({empty_note})")
        return

    debug(f"{title}: {n}")
    for x in items_list:
        debug(f"  - {_fmt(x)}")
