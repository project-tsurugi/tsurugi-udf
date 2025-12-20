# Copyright 2018-2025 Project Tsurugi.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
cmake_minimum_required(VERSION 3.15)
project(udf_plugin_viewer)

option(USE_INSTALLED_TSURUGI_UDF_COMMON
       "Use installed tsurugi-udf-common instead of source" ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(USE_INSTALLED_TSURUGI_UDF_COMMON)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)

  execute_process(
    COMMAND
      ${Python3_EXECUTABLE} -c
      "import tsurugi_udf_common, os; print(os.path.dirname(tsurugi_udf_common.__file__))"
    OUTPUT_VARIABLE TSURUGI_UDF_COMMON_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE)
  message(STATUS "TSURUGI_UDF_COMMON_DIR=${TSURUGI_UDF_COMMON_DIR}")
else()
  set(TSURUGI_UDF_COMMON_DIR
      "${CMAKE_CURRENT_SOURCE_DIR}/../common/tsurugi_udf_common")
endif()
message(STATUS "TSURUGI_UDF_COMMON_DIR=${TSURUGI_UDF_COMMON_DIR}")

set(TSURUGI_UDF_COMMON_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/../common/tsurugi_udf_common")

include_directories(${TSURUGI_UDF_COMMON_DIR}/include/udf)

find_package(pybind11 REQUIRED)
find_package(
  Python3
  COMPONENTS Interpreter Development
  REQUIRED)
list(APPEND CMAKE_MODULE_PATH "${TSURUGI_UDF_COMMON_DIR}/cmake")
find_package(nlohmann_json REQUIRED)
find_package(Protobuf REQUIRED)
find_package(gRPC REQUIRED)

pybind11_add_module(
  _udf_plugin bindings.cpp ${TSURUGI_UDF_COMMON_DIR}/src/udf/udf_loader.cpp
  ${TSURUGI_UDF_COMMON_DIR}/src/udf/error_info.cpp)

target_link_libraries(_udf_plugin PRIVATE ${GRPC_LIBRARIES}
                                          protobuf::libprotobuf)

install(TARGETS _udf_plugin LIBRARY DESTINATION udf_plugin_viewer)
