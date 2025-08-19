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
class ColumnDescriptor:
    index: int
    column_name: str
    type_kind: Optional[str] = None
    nested_record: Optional[RecordDescriptor] = None


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
