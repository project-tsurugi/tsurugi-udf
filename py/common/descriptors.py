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
    1: "FLOAT8",
    2: "FLOAT4",
    3: "INT8",
    4: "UINT8",
    5: "INT4",
    6: "FIXED8",
    7: "FIXED4",
    8: "BOOL",
    9: "STRING",
    10: "GROUP",
    11: "MESSAGE",
    12: "BYTES",
    13: "UINT4",
    14: "ENUM",
    15: "SFIXED4",
    16: "SFIXED8",
    17: "SINT4",
    18: "SINT8",
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
    "FLOAT8": "double",
    "FLOAT4": "float",
    "INT8": "int8",
    "UINT8": "uint8",
    "INT4": "int4",
    "FIXED8": "uint8",
    "FIXED4": "uint4",
    "BOOL": "bool",
    "STRING": "string",
    "BYTES": "string",
    "ENUM": "string",
    "GROUP": "/* no fetch, GROUP type */",
    "MESSAGE": "/* no fetch, MESSAGE type */",
    "UINT4": "uint4",
    "SINT4": "int4",
    "SINT8": "int8",
    "SFIXED8": "int8",
    "SFIXED4": "int4",
}
