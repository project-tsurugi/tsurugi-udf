cmake_minimum_required(VERSION 3.15)
project(udf_plugin LANGUAGES CXX)

# ============================================================
# Required variables (from build_with_cmake.py)
# ============================================================
if(NOT DEFINED BUILD_DIR)
  message(FATAL_ERROR "BUILD_DIR must be specified")
endif()

if(NOT DEFINED NAME)
  message(FATAL_ERROR "NAME must be specified (plugin name)")
endif()

if(NOT DEFINED TSURUGI_UDF_COMMON_DIR)
  message(FATAL_ERROR "TSURUGI_UDF_COMMON_DIR must be specified")
endif()

if(NOT DEFINED OUTPUT_DIR OR OUTPUT_DIR STREQUAL "")
  set(OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR})
endif()

# ============================================================
# C++ settings
# ============================================================
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================
# Use cmake modules shipped with tsurugi_udf_common
# ============================================================
list(APPEND CMAKE_MODULE_PATH "${TSURUGI_UDF_COMMON_DIR}/cmake")

message(STATUS "TSURUGI_UDF_COMMON_DIR=${TSURUGI_UDF_COMMON_DIR}")

# ============================================================
# Dependencies
# ============================================================
find_package(Protobuf REQUIRED)
find_package(gRPC REQUIRED)

# ============================================================
# Generated sources (from Python codegen)
# ============================================================
set(GENERATED_SOURCES_CMAKE "${BUILD_DIR}/generated_sources.cmake")

if(NOT EXISTS "${GENERATED_SOURCES_CMAKE}")
  message(
    FATAL_ERROR
      "generated_sources.cmake not found: ${GENERATED_SOURCES_CMAKE}\n"
      "Run Python code generation first.")
endif()

include("${GENERATED_SOURCES_CMAKE}")

message(STATUS "GENERATED_SRCS=${GENERATED_SRCS}")
message(STATUS "GENERATED_HDRS=${GENERATED_HDRS}")
message(STATUS "GENERATED_INCLUDE_DIRS=${GENERATED_INCLUDE_DIRS}")

# ============================================================
# Build shared library (.so)
# ============================================================
add_library(${NAME} SHARED ${GENERATED_SRCS} ${GENERATED_HDRS})

target_include_directories(
  ${NAME} PRIVATE ${GENERATED_INCLUDE_DIRS}
                  ${TSURUGI_UDF_COMMON_DIR}/include/udf ${GRPC_INCLUDE_DIRS})

target_link_libraries(${NAME} PRIVATE ${GRPC_LIBRARIES} protobuf::libprotobuf)

set_target_properties(${NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY
                                         "${OUTPUT_DIR}")

# ============================================================
# Summary
# ============================================================
message(STATUS "========================================")
message(STATUS "Plugin name      : ${NAME}")
message(STATUS "Build dir        : ${BUILD_DIR}")
message(STATUS "Output directory : ${OUTPUT_DIR}")
message(STATUS "========================================")
