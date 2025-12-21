cmake_minimum_required(VERSION 3.15)
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
# tsurugi_udf_common location
# ------------------------------------------------------------
if(DEFINED SKBUILD)
  message(STATUS "Detected pip / scikit-build environment")
  set(USE_INSTALLED_TSURUGI_UDF_COMMON OFF)
else()
  option(
    USE_INSTALLED_TSURUGI_UDF_COMMON
    "Use installed tsurugi-udf-common instead of source tree"
    ON)
endif()

if(USE_INSTALLED_TSURUGI_UDF_COMMON)
  execute_process(
    COMMAND
      ${Python3_EXECUTABLE} -c
      "import tsurugi_udf_common, os; print(os.path.dirname(tsurugi_udf_common.__file__))"
    OUTPUT_VARIABLE TSURUGI_UDF_COMMON_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE _import_result)
  if(NOT _import_result EQUAL 0)
    message(FATAL_ERROR "tsurugi_udf_common not importable")
  endif()
else()
  set(TSURUGI_UDF_COMMON_DIR
      "${CMAKE_CURRENT_SOURCE_DIR}/../../common/tsurugi_udf_common")
endif()

message(STATUS "TSURUGI_UDF_COMMON_DIR=${TSURUGI_UDF_COMMON_DIR}")

# ------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------
find_package(nlohmann_json CONFIG REQUIRED)
find_package(Protobuf REQUIRED)

find_package(gRPC CONFIG QUIET)

set(HAVE_GRPC OFF)
if(gRPC_FOUND)
  message(STATUS "gRPC found via CMake config")
  set(HAVE_GRPC ON)
else()
  message(STATUS "gRPCConfig.cmake not found, falling back to system libs")
  find_library(GRPC_LIB grpc)
  find_library(GRPCPP_LIB grpc++)
  if(GRPC_LIB AND GRPCPP_LIB)
    set(HAVE_GRPC ON)
  endif()
endif()

# ------------------------------------------------------------
# Python module (_udf_plugin)
# ------------------------------------------------------------
pybind11_add_module(
  _udf_plugin
  ${CMAKE_CURRENT_SOURCE_DIR}/tsurugi_udf/viewer/udf_plugin_viewer/bindings.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/tsurugi_udf/common/tsurugi_udf_common/src/udf/udf_loader.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/tsurugi_udf/common/tsurugi_udf_common/src/udf/error_info.cpp
)

target_include_directories(
  _udf_plugin
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/tsurugi_udf/common/tsurugi_udf_common/include/udf
)

target_link_libraries(
  _udf_plugin
  PRIVATE
    protobuf::libprotobuf
    nlohmann_json::nlohmann_json
)

if(HAVE_GRPC)
  target_compile_definitions(_udf_plugin PRIVATE TSURUGI_HAVE_GRPC=1)
  if(gRPC_FOUND)
    target_link_libraries(_udf_plugin PRIVATE gRPC::grpc++ gRPC::grpc)
  else()
    target_link_libraries(_udf_plugin PRIVATE ${GRPCPP_LIB} ${GRPC_LIB})
  endif()
else()
  message(WARNING "Building without gRPC support")
endif()

# ------------------------------------------------------------
# install (Python package layout)
# ------------------------------------------------------------
install(
  TARGETS _udf_plugin
  LIBRARY DESTINATION tsurugi_udf/viewer/udf_plugin_viewer
)
