from pathlib import Path
import sys


def _die(msg: str):
    raise SystemExit(msg)


def dedup_keep_order(xs):
    seen = set()
    out = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def validate_includes(includes):
    includes = dedup_keep_order(includes or [])
    bad = []
    for inc in includes:
        p = Path(inc)
        if not p.exists() or not p.is_dir():
            bad.append(inc)
    if bad:
        _die("-I/--include must be existing directories:\n  - " + "\n  - ".join(bad))
    return includes


def validate_proto_files(proto_files):
    bad = []
    out = []
    for p in proto_files:
        if not p.exists():
            bad.append(f"{p} (not found)")
        elif not p.is_file():
            bad.append(f"{p} (not a file; did you mean -I?)")
        elif p.suffix != ".proto":
            bad.append(f"{p} (not .proto)")
        else:
            out.append(p)
    if bad:
        _die("--proto must be existing .proto files:\n  - " + "\n  - ".join(bad))
    return out
