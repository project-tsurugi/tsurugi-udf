# Copyright 2018-2025 Project Tsurugi.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Version:
    major: int = 1
    minor: int = 0
    patch: int = 0


@dataclass
class ColumnDescriptor:
    index: int
    column_name: str
    type_kind: Optional[str] = None
    nested_record: Optional[RecordDescriptor] = None
    oneof_index: Optional[int] = None
    oneof_name: Optional[str] = None


@dataclass
class RecordDescriptor:
    columns: List[ColumnDescriptor]
    record_name: str = ""

    def __post_init__(self):
        if self.columns is None:
            self.columns = []


@dataclass
class FunctionDescriptor:
    function_index: int
    function_name: str
    function_kind: str
    input_record: RecordDescriptor
    output_record: RecordDescriptor


@dataclass
class ServiceDescriptor:
    service_index: int
    service_name: str
    functions: List[FunctionDescriptor]


@dataclass
class PackageDescriptor:
    package_name: str
    services: List[ServiceDescriptor]
    file_name: Optional[str] = None
    version: Version = Version()


# @see https://github.com/protocolbuffers/protobuf/blob/main/src/google/protobuf/descriptor.proto#L243
FIELD_TYPE_MAP = {
    1: "float8",
    2: "float4",
    3: "int8",
    4: "uint8",
    5: "int4",
    6: "fixed8",
    7: "fixed4",
    8: "boolean",
    9: "string",
    10: "group",
    11: "message",
    12: "bytes",
    13: "uint4",
    14: "grpc_enum",
    15: "sfixed4",
    16: "sfixed8",
    17: "sint4",
    18: "sint8",
}
# @see https://protobuf.dev/programming-guides/proto3/#scalar
# internal type name -> C++ fetch name
# sint32	int32_t
# sint64	int64_t
# fixed32	uint32_t
# fixed32	uint64_t
# sfixed32	int32_t
# sfixed64	int64_t
TYPE_KIND_MAP = {
    "float8": "double",
    "float4": "float",
    "int8": "int8",
    "uint8": "uint8",
    "int4": "int4",
    "fixed8": "uint8",
    "fixed4": "uint4",
    "boolean": "bool",
    "string": "string",
    "bytes": "string",
    "grpc_enum": "string",
    "group": "/* no fetch, GROUP type */",
    "message": "/* no fetch, MESSAGE type */",
    "uint4": "uint4",
    "sint4": "int4",
    "sint8": "int8",
    "sfixed8": "int8",
    "sfixed4": "int4",
}
