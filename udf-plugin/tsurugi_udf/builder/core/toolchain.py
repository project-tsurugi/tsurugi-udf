from __future__ import annotations

import os
import shlex
import subprocess
import logging

logger = logging.getLogger(__name__)
DEFAULT_CXX = "g++"
PKG_CONFIG_PACKAGES = ["protobuf", "grpc++"]


def get_cxx() -> str:
    """Return the C++ compiler command used by the builder."""
    return os.environ.get("CXX", DEFAULT_CXX)


def get_cxxflags() -> list[str]:
    """Return common C++ compile flags."""
    return shlex.split(os.environ.get("CXXFLAGS", "")) + pkg_config_cflags()


def get_ldflags() -> list[str]:
    """Return common C++ link flags."""
    return dedup_keep_order(
        shlex.split(os.environ.get("LDFLAGS", "")) + pkg_config_libs()
    )


def pkg_config_cflags() -> list[str]:
    return _pkg_config("--cflags")


def pkg_config_libs() -> list[str]:
    return _pkg_config("--libs")


def _pkg_config(option: str) -> list[str]:
    try:
        r = subprocess.run(
            ["pkg-config", option, *PKG_CONFIG_PACKAGES],
            check=True,
            text=True,
            capture_output=True,
        )
        out = r.stdout.strip()
        return shlex.split(out) if out else []

    except FileNotFoundError:
        logger.debug("pkg-config not found")
        return []

    except subprocess.CalledProcessError as e:
        logger.debug("pkg-config failed: %s", e)
        return []


def dedup_keep_order(xs: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in xs:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out
