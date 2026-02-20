from pathlib import Path
from google.protobuf.descriptor_pb2 import FileDescriptorSet


def load_fds(desc_pb: Path) -> FileDescriptorSet:
    fds = FileDescriptorSet()
    fds.ParseFromString(desc_pb.read_bytes())
    return fds


def build_import_graph(fds: FileDescriptorSet) -> dict[str, set[str]]:
    return {fd.name: set(fd.dependency) for fd in fds.file}
