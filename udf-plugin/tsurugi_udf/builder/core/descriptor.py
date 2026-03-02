from pathlib import Path
from google.protobuf.descriptor_pb2 import FileDescriptorSet


def load_fds(desc_pb: Path) -> FileDescriptorSet:
    fds = FileDescriptorSet()
    fds.ParseFromString(desc_pb.read_bytes())
    return fds


def build_import_graph(fds: FileDescriptorSet) -> dict[str, set[str]]:
    return {fd.name: set(fd.dependency) for fd in fds.file}


def normalize_proto_arg_to_fd_name(
    proto_path: Path, includes: list[Path]
) -> str | None:
    p = proto_path.resolve()
    for inc in includes:
        inc = Path(inc).resolve()
        try:
            rel = p.relative_to(inc)
            return rel.as_posix()
        except ValueError:
            continue
    return None


def find_unlisted_imports(
    *,
    fds: FileDescriptorSet,
    includes: list[Path],
    proto_files: list[Path],
    exclude_well_known: bool = True,
) -> tuple[list[str], list[str]]:

    resolved = {fd.name for fd in fds.file}

    specified: set[str] = set()
    unmappable: list[str] = []
    for pf in proto_files:
        name = normalize_proto_arg_to_fd_name(pf, includes)
        if name is None:
            unmappable.append(str(pf))
        else:
            specified.add(name)

    def is_well_known(n: str) -> bool:
        return n.startswith("google/protobuf/")

    unlisted = resolved - specified
    if exclude_well_known:
        unlisted = {n for n in unlisted if not is_well_known(n)}

    return (unmappable, sorted(unlisted))
