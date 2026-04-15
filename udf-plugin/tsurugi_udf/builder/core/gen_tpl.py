from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from .log import debug

TEMPLATE = {
    "plugin_api_impl.cpp.j2": "plugin_api_impl.cpp",
    "rpc_client.cpp.j2": "rpc_client.cpp",
    "rpc_client.h.j2": "rpc_client.h",
    "rpc_client_factory.cpp.j2": "rpc_client_factory.cpp",
}

SPECIAL_RECORDS = {
    "tsurugidb.udf.Decimal": {
        "special_record_kind": "decimal",
        "special_fetch_name": "decimal",
        "cpp_value_type": "decimal_value",
        "fields": [
            {"name": "unscaled_value", "getter": "unscaled_value()"},
            {"name": "exponent", "getter": "exponent()"},
        ],
    },
    "tsurugidb.udf.Date": {
        "special_record_kind": "date",
        "special_fetch_name": "date",
        "cpp_value_type": "date_value",
        "fields": [
            {"name": "days", "getter": "days()"},
        ],
    },
    "tsurugidb.udf.LocalTime": {
        "special_record_kind": "local_time",
        "special_fetch_name": "local_time",
        "cpp_value_type": "local_time_value",
        "fields": [
            {"name": "nanos", "getter": "nanos()"},
        ],
    },
    "tsurugidb.udf.LocalDatetime": {
        "special_record_kind": "local_datetime",
        "special_fetch_name": "local_datetime",
        "cpp_value_type": "local_datetime_value",
        "fields": [
            {"name": "offset_seconds", "getter": "offset_seconds()"},
            {"name": "nano_adjustment", "getter": "nano_adjustment()"},
        ],
    },
    "tsurugidb.udf.OffsetDatetime": {
        "special_record_kind": "offset_datetime",
        "special_fetch_name": "offset_datetime",
        "cpp_value_type": "offset_datetime_value",
        "fields": [
            {"name": "offset_seconds", "getter": "offset_seconds()"},
            {"name": "nano_adjustment", "getter": "nano_adjustment()"},
            {"name": "time_zone_offset", "getter": "time_zone_offset()"},
        ],
    },
    "tsurugidb.udf.BlobReference": {
        "special_record_kind": "blob_reference",
        "special_fetch_name": "blob_reference",
        "cpp_value_type": "blob_reference_value",
        "fields": [
            {"name": "storage_id", "getter": "storage_id()"},
            {"name": "object_id", "getter": "object_id()"},
            {"name": "tag", "getter": "tag()"},
            {"name": "provisioned", "getter": "provisioned()"},
        ],
    },
    "tsurugidb.udf.ClobReference": {
        "special_record_kind": "clob_reference",
        "special_fetch_name": "clob_reference",
        "cpp_value_type": "clob_reference_value",
        "fields": [
            {"name": "storage_id", "getter": "storage_id()"},
            {"name": "object_id", "getter": "object_id()"},
            {"name": "tag", "getter": "tag()"},
            {"name": "provisioned", "getter": "provisioned()"},
        ],
    },
}


def _camelcase(s: str) -> str:
    parts = s.split("_")
    return "".join(p.capitalize() for p in parts if p)


def _has_service(fd) -> bool:
    return len(fd.service) > 0


def _default_fetch_add_name(type_kind: str) -> str:
    k = (type_kind or "").lower()
    m = {
        "int4": "int4",
        "sfixed4": "int4",
        "sint4": "int4",
        "uint4": "uint4",
        "fixed4": "uint4",
        "int8": "int8",
        "sfixed8": "int8",
        "sint8": "int8",
        "uint8": "uint8",
        "fixed8": "uint8",
        "float4": "float",
        "float8": "double",
        "boolean": "bool",
        "string": "string",
        "bytes": "bytes",
    }
    return m.get(k, "/* no fetch, unknown type */")


def split_fds_by_proto_with_service(fds: FileDescriptorSet) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = {}
    message_type_map = {}

    def register_message(pkg: str, msg, parent_prefix: str = ""):
        if parent_prefix:
            fqname = f"{parent_prefix}.{msg.name}"
        else:
            fqname = f".{pkg}.{msg.name}" if pkg else f".{msg.name}"
        message_type_map[fqname] = msg
        for nested in msg.nested_type:
            register_message(pkg, nested, fqname)

    for fd in fds.file:
        for msg in fd.message_type:
            register_message(fd.package, msg)

    FIELD_TYPE = {
        1: "float8",
        2: "float4",
        3: "int8",
        4: "uint8",
        5: "int4",
        6: "fixed8",
        7: "fixed4",
        8: "boolean",
        9: "string",
        12: "bytes",
        13: "uint4",
        15: "sfixed4",
        16: "sfixed8",
        17: "sint4",
        18: "sint8",
        11: "message",
    }
    RUNTIME_KIND = {
        "boolean": "boolean",
        "int4": "int4",
        "fixed4": "uint4",
        "uint4": "uint4",
        "sint4": "int4",
        "sfixed4": "int4",
        "int8": "int8",
        "fixed8": "uint8",
        "uint8": "uint8",
        "sint8": "int8",
        "sfixed8": "int8",
        "float4": "float4",
        "float8": "float8",
        "string": "string",
        "bytes": "bytes",
    }

    def resolve_record(type_name: str) -> dict:
        d = message_type_map.get(type_name)
        record_name = type_name.lstrip(".")
        special = SPECIAL_RECORDS.get(record_name)
        if not d:
            return {
                "record_name": record_name,
                "special_record_kind": (
                    special["special_record_kind"] if special else None
                ),
                "special_fetch_name": (
                    special["special_fetch_name"] if special else None
                ),
                "cpp_value_type": special["cpp_value_type"] if special else None,
                "special_fields": special["fields"] if special else [],
                "columns": [
                    {
                        "index": 0,
                        "column_name": "unknown",
                        "type_kind": "UNKNOWN",
                        "nested_record": None,
                        "oneof_index": None,
                        "oneof_name": None,
                        "proto3_optional": False,
                    }
                ],
                "oneof_groups": [],
            }

        cols = []
        oneof_groups = []
        oneof_groups_by_index = {}

        for idx, field in enumerate(d.field):
            kind = FIELD_TYPE.get(field.type, f"TYPE_{field.type}")
            oneof_idx = field.oneof_index if field.HasField("oneof_index") else None
            oneof_name = d.oneof_decl[oneof_idx].name if oneof_idx is not None else None
            nested = None
            special_kind = None
            special_fetch_name = None
            cpp_value_type = None
            special_fields = []

            if kind == "message":
                nested = resolve_record(field.type_name)
                special_kind = nested.get("special_record_kind")
                special_fetch_name = nested.get("special_fetch_name")
                cpp_value_type = nested.get("cpp_value_type")
                special_fields = nested.get("special_fields", [])

            runtime_kind = special_kind or RUNTIME_KIND.get(kind)
            is_user_oneof_member = oneof_idx is not None and not field.proto3_optional
            col = {
                "index": idx,
                "column_name": field.name,
                "type_kind": kind,
                "runtime_kind": runtime_kind,
                "nested_record": nested,
                "oneof_index": oneof_idx,
                "oneof_name": oneof_name,
                "proto3_optional": field.proto3_optional,
                "is_user_oneof_member": is_user_oneof_member,
                "special_record_kind": special_kind,
                "special_fetch_name": special_fetch_name,
                "cpp_value_type": cpp_value_type,
                "special_fields": special_fields,
            }
            cols.append(col)
            if is_user_oneof_member:
                group = oneof_groups_by_index.get(oneof_idx)
                if group is None:
                    group = {
                        "oneof_index": oneof_idx,
                        "oneof_name": oneof_name,
                        "members": [],
                    }
                    oneof_groups_by_index[oneof_idx] = group
                    oneof_groups.append(group)
                group["members"].append(col)

        for group in oneof_groups:
            seen_runtime_kinds = {}
            for member in group["members"]:
                runtime_kind = member["runtime_kind"]
                if runtime_kind is None:
                    raise ValueError(
                        f"Unsupported oneof member type '{member['type_kind']}' in {type_name}.{member['column_name']}"
                    )
                other = seen_runtime_kinds.get(runtime_kind)
                if other is not None:
                    raise ValueError(
                        f"Ambiguous oneof runtime kind '{runtime_kind}' in {type_name}.{group['oneof_name']}: {other} and {member['column_name']}"
                    )
                seen_runtime_kinds[runtime_kind] = member["column_name"]

        return {
            "record_name": record_name,
            "special_record_kind": special["special_record_kind"] if special else None,
            "special_fetch_name": special["special_fetch_name"] if special else None,
            "cpp_value_type": special["cpp_value_type"] if special else None,
            "special_fields": special["fields"] if special else [],
            "columns": cols,
            "oneof_groups": oneof_groups,
        }

    service_counter = 0
    function_counter = 0

    for fd in fds.file:
        if not _has_service(fd):
            continue

        pkg_name = fd.package
        services = []
        for svc in fd.service:
            functions = []
            for m in svc.method:
                kind = "unary"
                if m.client_streaming and m.server_streaming:
                    kind = "bidirectional_streaming"
                elif m.client_streaming:
                    kind = "client_streaming"
                elif m.server_streaming:
                    kind = "server_streaming"

                functions.append(
                    {
                        "function_index": function_counter,
                        "function_name": m.name,
                        "function_kind": kind,
                        "input_record": resolve_record(m.input_type),
                        "output_record": resolve_record(m.output_type),
                    }
                )
                function_counter += 1

            services.append(
                {
                    "service_index": service_counter,
                    "service_name": svc.name,
                    "functions": functions,
                }
            )
            service_counter += 1

        pkg = {
            "package_name": pkg_name,
            "file_name": fd.name,
            "version": {"major": 0, "minor": 3, "patch": 1},
            "services": services,
        }
        out.setdefault(fd.name, []).append(pkg)

    return out


def render_tpl_for_rpc_protos(
    *,
    fds: FileDescriptorSet,
    templates_dir: Path,
    tpl_dir: Path,
    fetch_add_name=None,
) -> Dict[str, Dict[str, Path]]:
    tpl_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["camelcase"] = _camelcase
    env.globals["fetch_add_name"] = fetch_add_name or _default_fetch_add_name

    file_to_packages = split_fds_by_proto_with_service(fds)

    out: Dict[str, Dict[str, Path]] = {}

    for proto_file, packages in file_to_packages.items():
        stem = Path(proto_file).stem

        subdir = tpl_dir / stem
        subdir.mkdir(parents=True, exist_ok=True)

        out[proto_file] = {}

        for tpl_name, out_name in TEMPLATE.items():
            gen = subdir / out_name

            template = env.get_template(tpl_name)
            rendered = template.render(
                packages=packages,
                proto_base_name=stem,
            )
            gen.write_text(rendered)
            out[proto_file][out_name] = gen

        created = sorted(p.name for p in out[proto_file].values())
        debug(
            f"generated RPC templates: proto='{proto_file}' dir='{subdir}' files={len(created)}"
        )
        for name in created:
            debug(f"  - {name}")

    return out
