from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    FieldDescriptorProto,
    FileDescriptorProto,
    FileDescriptorSet,
)

TYPE_TO_CATEGORY = {
    FieldDescriptorProto.TYPE_INT32: "int",
    FieldDescriptorProto.TYPE_SINT32: "int",
    FieldDescriptorProto.TYPE_SFIXED32: "int",
    FieldDescriptorProto.TYPE_UINT32: "int",
    FieldDescriptorProto.TYPE_FIXED32: "int",
    FieldDescriptorProto.TYPE_INT64: "bigint",
    FieldDescriptorProto.TYPE_SINT64: "bigint",
    FieldDescriptorProto.TYPE_SFIXED64: "bigint",
    FieldDescriptorProto.TYPE_UINT64: "bigint",
    FieldDescriptorProto.TYPE_FIXED64: "bigint",
    FieldDescriptorProto.TYPE_FLOAT: "float4",
    FieldDescriptorProto.TYPE_DOUBLE: "float8",
    FieldDescriptorProto.TYPE_STRING: "string",
    FieldDescriptorProto.TYPE_BYTES: "bytes",
}

TYPE_NAME = {
    FieldDescriptorProto.TYPE_DOUBLE: "double",
    FieldDescriptorProto.TYPE_FLOAT: "float",
    FieldDescriptorProto.TYPE_INT64: "int64",
    FieldDescriptorProto.TYPE_UINT64: "uint64",
    FieldDescriptorProto.TYPE_INT32: "int32",
    FieldDescriptorProto.TYPE_FIXED64: "fixed64",
    FieldDescriptorProto.TYPE_FIXED32: "fixed32",
    FieldDescriptorProto.TYPE_BOOL: "bool",
    FieldDescriptorProto.TYPE_STRING: "string",
    FieldDescriptorProto.TYPE_MESSAGE: "message",
    FieldDescriptorProto.TYPE_BYTES: "bytes",
    FieldDescriptorProto.TYPE_UINT32: "uint32",
    FieldDescriptorProto.TYPE_ENUM: "enum",
    FieldDescriptorProto.TYPE_SFIXED32: "sfixed32",
    FieldDescriptorProto.TYPE_SFIXED64: "sfixed64",
    FieldDescriptorProto.TYPE_SINT32: "sint32",
    FieldDescriptorProto.TYPE_SINT64: "sint64",
}


@dataclass(frozen=True)
class ValidationIssue:
    location: str
    message: str


def _field_type_label(field: FieldDescriptorProto) -> str:
    if field.type == FieldDescriptorProto.TYPE_MESSAGE:
        return field.type_name.lstrip(".")
    return TYPE_NAME.get(field.type, f"TYPE_{field.type}")


def _field_signature(field: FieldDescriptorProto) -> str:
    return f"{field.name} ({_field_type_label(field)})"


def _build_message_index(
    fds: FileDescriptorSet,
) -> dict[str, tuple[FileDescriptorProto, DescriptorProto]]:
    index: dict[str, tuple[FileDescriptorProto, DescriptorProto]] = {}

    def register(fd: FileDescriptorProto, msg: DescriptorProto, prefix: str) -> None:
        fqname = f"{prefix}.{msg.name}" if prefix else msg.name
        index[f".{fqname}"] = (fd, msg)
        for nested in msg.nested_type:
            register(fd, nested, fqname)

    for fd in fds.file:
        prefix = fd.package or ""
        for msg in fd.message_type:
            register(fd, msg, prefix)

    return index


def _build_source_locations(
    fds: FileDescriptorSet,
) -> dict[tuple[str, tuple[int, ...]], str]:
    result: dict[tuple[str, tuple[int, ...]], str] = {}

    for fd in fds.file:
        file_name = fd.name or "<unknown>"
        for loc in fd.source_code_info.location:
            if not loc.path:
                continue

            if len(loc.span) >= 3:
                line = loc.span[0] + 1
                col = loc.span[1] + 1
                text = f"{file_name}:{line}:{col}"
            else:
                text = file_name

            result[(file_name, tuple(loc.path))] = text

    return result


def _best_effort_location(
    source_locations: dict[tuple[str, tuple[int, ...]], str],
    fd: FileDescriptorProto,
    candidate_paths: list[list[int]],
) -> str:
    file_name = fd.name or "<unknown>"
    for path in candidate_paths:
        loc = source_locations.get((file_name, tuple(path)))
        if loc:
            return loc
    return file_name


def validate_oneof_categories(fds: FileDescriptorSet) -> None:
    issues: list[ValidationIssue] = []
    source_locations = _build_source_locations(fds)
    message_index = _build_message_index(fds)

    def add_issue(location: str, message: str) -> None:
        issues.append(ValidationIssue(location=location, message=message))

    def check_message(
        fd: FileDescriptorProto,
        msg: DescriptorProto,
        prefix: str,
        path: list[int],
    ) -> None:
        msg_name = f"{prefix}.{msg.name}" if prefix else msg.name

        groups: dict[int, dict[str, object]] = {}
        for idx, oneof in enumerate(msg.oneof_decl):
            groups[idx] = {
                "name": oneof.name,
                "fields": [],
                "path": path + [8, idx],  # DescriptorProto.oneof_decl
            }

        for field in msg.field:
            if field.HasField("oneof_index") and not field.proto3_optional:
                groups[field.oneof_index]["fields"].append(field)

        for group in groups.values():
            group_name = group["name"]
            fields = group["fields"]
            group_path = group["path"]
            location = _best_effort_location(
                source_locations,
                fd,
                [
                    group_path,  # oneof declaration
                    path,  # enclosing message
                    [],  # file
                ],
            )

            cat_map: dict[str, list[FieldDescriptorProto]] = defaultdict(list)
            msg_map: dict[str, list[FieldDescriptorProto]] = defaultdict(list)

            for field in fields:
                if field.type == FieldDescriptorProto.TYPE_MESSAGE:
                    msg_type = field.type_name.lstrip(".")
                    msg_map[msg_type].append(field)
                else:
                    cat = TYPE_TO_CATEGORY.get(field.type)
                    if cat:
                        cat_map[cat].append(field)

            for cat, flist in cat_map.items():
                if len(flist) > 1:
                    names = ", ".join(_field_signature(f) for f in flist)
                    add_issue(
                        location,
                        f"Invalid oneof '{msg_name}.{group_name}': {names} "
                        f"are all internal type '{cat}'. "
                        f"Only one '{cat}' field is allowed in the same oneof.",
                    )

            for mtype, flist in msg_map.items():
                if len(flist) > 1:
                    names = ", ".join(_field_signature(f) for f in flist)
                    add_issue(
                        location,
                        f"Invalid oneof '{msg_name}.{group_name}': {names} "
                        f"are all message type '{mtype}'. "
                        f"Only one field of the same message type is allowed in the same oneof.",
                    )

        for nested_idx, nested in enumerate(msg.nested_type):
            check_message(fd, nested, msg_name, path + [3, nested_idx])  # nested_type

    def message_has_user_oneof(msg: DescriptorProto) -> bool:
        for field in msg.field:
            if field.HasField("oneof_index") and not field.proto3_optional:
                return True
        return False

    for fd in fds.file:
        prefix = fd.package or ""
        for msg_idx, msg in enumerate(fd.message_type):
            check_message(
                fd, msg, prefix, [4, msg_idx]
            )  # FileDescriptorProto.message_type

    for fd in fds.file:
        prefix = fd.package or ""
        for svc_idx, svc in enumerate(fd.service):
            svc_name = f"{prefix}.{svc.name}" if prefix else svc.name
            for method_idx, method in enumerate(svc.method):
                output = message_index.get(method.output_type)
                if output is None:
                    continue

                _, out_msg = output
                if not message_has_user_oneof(out_msg):
                    continue

                location = _best_effort_location(
                    source_locations,
                    fd,
                    [
                        [6, svc_idx, 2, method_idx],  # method
                        [6, svc_idx],  # service
                        [],  # file
                    ],
                )
                output_name = method.output_type.lstrip(".")
                add_issue(
                    location,
                    f"Invalid RPC return type '{output_name}' in '{svc_name}.{method.name}': "
                    "oneof is not allowed in return messages.",
                )

    if issues:
        lines = ["oneof validation failed:"]
        for issue in issues:
            lines.append(f"  - {issue.location}: {issue.message}")
        raise ValueError("\n".join(lines))
