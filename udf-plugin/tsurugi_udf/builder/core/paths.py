from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BuildPaths:
    build_dir: Path
    OUT: Path
    GEN: Path
    OBJ: Path
    TPL: Path
    LIB: Path
    INI: Path
    CMN: Path

    @classmethod
    def from_build_dir(cls, build_dir: Path) -> "BuildPaths":
        return cls(
            build_dir=build_dir,
            OUT=build_dir / "desc",
            GEN=build_dir / "gen",
            OBJ=build_dir / "obj",
            TPL=build_dir / "tpl",
            LIB=build_dir / "lib",
            INI=build_dir / "ini",
            CMN=build_dir / "cmn",
        )
