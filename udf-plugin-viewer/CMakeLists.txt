# Copyright 2018-2025 Project Tsurugi.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
cmake_minimum_required(VERSION 3.14)
project(udf_plugin_viewer)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(${CMAKE_SOURCE_DIR}/../include)

find_package(pybind11 REQUIRED)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(nlohmann_json REQUIRED)

pybind11_add_module(udf_plugin
    bindings.cpp
    ${CMAKE_SOURCE_DIR}/../src/udf/udf_loader.cpp
)

add_custom_command(
  OUTPUT ${CMAKE_CURRENT_SOURCE_DIR}/udf_plugin_viewer/descriptors.py
  COMMAND ${CMAKE_COMMAND} -E copy
    ${CMAKE_SOURCE_DIR}/../py/common/descriptors.py
    ${CMAKE_CURRENT_SOURCE_DIR}/udf_plugin_viewer/descriptors.py
  DEPENDS ${CMAKE_SOURCE_DIR}/../py/common/descriptors.py
)

add_custom_target(copy_descriptors ALL
  DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/udf_plugin_viewer/descriptors.py
)

add_dependencies(udf_plugin copy_descriptors)

add_custom_command(
    TARGET udf_plugin POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:udf_plugin>
        ${CMAKE_CURRENT_SOURCE_DIR}/udf_plugin_viewer/$<TARGET_FILE_NAME:udf_plugin>
    COMMENT "Copying udf_plugin shared library to udf_plugin_viewer/"
)
