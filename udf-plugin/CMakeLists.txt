cmake_minimum_required(VERSION 3.20)
project(udf_plugin_viewer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ------------------------------------------------------------
# Python / pybind11
# ------------------------------------------------------------
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

# ------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------
find_package(nlohmann_json CONFIG REQUIRED)
find_package(Protobuf REQUIRED)

# ------------------------------------------------------------
# Python module (_udf_plugin)
# ------------------------------------------------------------
pybind11_add_module(
  _udf_plugin
  ${CMAKE_CURRENT_SOURCE_DIR}/tsurugi_udf/viewer/udf_plugin_viewer/bindings.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/tsurugi_udf/common/tsurugi_udf_common/src/udf/viewer_loader.cpp
)

target_include_directories(
  _udf_plugin
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/tsurugi_udf/common/tsurugi_udf_common/include/udf
)

target_link_libraries(_udf_plugin PRIVATE protobuf::libprotobuf
                                          nlohmann_json::nlohmann_json)

# ------------------------------------------------------------
# install (Python package layout)
# ------------------------------------------------------------
install(TARGETS _udf_plugin
        LIBRARY DESTINATION tsurugi_udf/viewer/udf_plugin_viewer)
