from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from jinja2 import Environment, FileSystemLoader
from google.protobuf.descriptor_pb2 import FileDescriptorSet
from .log import info

TEMPLATE = {
    "plugin_api_impl.cpp.j2": "plugin_api_impl.cpp",
    "rpc_client.cpp.j2": "rpc_client.cpp",
    "rpc_client.h.j2": "rpc_client.h",
    "rpc_client_factory.cpp.j2": "rpc_client_factory.cpp",
}


def _camelcase(s: str) -> str:
    parts = s.split("_")
    return "".join(p.capitalize() for p in parts if p)


def _has_service(fd) -> bool:
    return len(fd.service) > 0


def _default_fetch_add_name(type_kind: str) -> str:
    k = (type_kind or "").lower()
    m = {
        # ints
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
        "float": "float",
        "double": "double",
        "boolean": "bool",
        "string": "string",
        "bytes": "string",
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
        1: "double",
        2: "float",
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

    def resolve_record(type_name: str) -> dict:
        d = message_type_map.get(type_name)
        if not d:
            return {
                "record_name": type_name.lstrip("."),
                "columns": [
                    {
                        "index": 0,
                        "column_name": "unknown",
                        "type_kind": "UNKNOWN",
                        "nested_record": None,
                        "oneof_index": None,
                        "oneof_name": None,
                    }
                ],
            }
        cols = []
        for idx, field in enumerate(d.field):
            kind = FIELD_TYPE.get(field.type, f"TYPE_{field.type}")
            oneof_idx = field.oneof_index if field.HasField("oneof_index") else None
            oneof_name = d.oneof_decl[oneof_idx].name if oneof_idx is not None else None
            nested = None
            if kind == "message":
                nested = resolve_record(field.type_name)
            cols.append(
                {
                    "index": idx,
                    "column_name": field.name,
                    "type_kind": kind,
                    "nested_record": nested,
                    "oneof_index": oneof_idx,
                    "oneof_name": oneof_name,
                }
            )
        return {"record_name": type_name.lstrip("."), "columns": cols}

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
            "version": {"major": 0, "minor": 1, "patch": 1},
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
        created = [p.name for p in out[proto_file].values()]
        created.sort()
        info(f"generated RPC templates for proto '{proto_file}' -> {subdir}")
        for name in created:
            info(f"  - {name}")

    return out
