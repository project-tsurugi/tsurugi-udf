cmake_minimum_required(VERSION 3.15)
project(udf_app)

# ============================================================
# Options
# ============================================================
option(USE_INSTALLED_TSURUGI_UDF_COMMON
       "Use installed tsurugi-udf-common instead of source" ON)

option(ENABLE_TESTS "Build tests" OFF)
option(ENABLE_UNARY_TEST "Build unary_test" OFF)
option(ENABLE_LOAD_ANOTHER_TEST "Build load_another_test" OFF)
option(ENABLE_ONEOF_TEST "Build oneof_test" OFF)
option(ENABLE_NESTED_TEST "Build nested_test" OFF)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PROJECT_ROOT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../..)
set(TEST_ROOT_DIR ${PROJECT_ROOT_DIR}/test)

# ============================================================
# Locate tsurugi_udf_common
# ============================================================
if(USE_INSTALLED_TSURUGI_UDF_COMMON)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
  execute_process(
    COMMAND
      ${Python3_EXECUTABLE} -c
      "import tsurugi_udf_common, os, sys; sys.stdout.write(os.path.dirname(tsurugi_udf_common.__file__))"
    OUTPUT_VARIABLE TSURUGI_UDF_COMMON_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE)
else()
  set(TSURUGI_UDF_COMMON_DIR "${PROJECT_ROOT_DIR}/common/tsurugi_udf_common")
endif()

message(STATUS "TSURUGI_UDF_COMMON_DIR=${TSURUGI_UDF_COMMON_DIR}")

# ============================================================
# Find dependencies
# ============================================================
list(APPEND CMAKE_MODULE_PATH "${TSURUGI_UDF_COMMON_DIR}/cmake")

find_package(Protobuf REQUIRED)
find_package(gRPC REQUIRED)
find_package(Python3 REQUIRED)
find_program(PROTOC_EXECUTABLE protoc)
find_package(Boost REQUIRED)

if(NOT PROTOC_EXECUTABLE)
  message(FATAL_ERROR "protoc not found!")
endif()

find_program(GRPC_CPP_PLUGIN_EXECUTABLE grpc_cpp_plugin)
if(NOT GRPC_CPP_PLUGIN_EXECUTABLE)
  message(FATAL_ERROR "grpc_cpp_plugin not found!")
endif()

set(GENERATE_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/../generate.py)

# ============================================================
# Build type
# ============================================================
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Debug)
endif()

# ============================================================
# Proto files
# ============================================================

if(ENABLE_UNARY_TEST)
  set(PROTO_PATH ${TEST_ROOT_DIR}/unary_test/proto)
  set(PROTO_FILES ${TEST_ROOT_DIR}/unary_test/proto/test_all.proto)
elseif(ENABLE_LOAD_ANOTHER_TEST)
  set(PROTO_PATH ${TEST_ROOT_DIR}/load_another/proto)
  set(PROTO_FILES ${TEST_ROOT_DIR}/load_another/proto/sample.proto)
elseif(ENABLE_ONEOF_TEST)
  set(PROTO_PATH ${TEST_ROOT_DIR}/oneof_test/proto)
  set(PROTO_FILES ${TEST_ROOT_DIR}/oneof_test/proto/oneof_test.proto)
elseif(ENABLE_NESTED_TEST)
  set(PROTO_PATH ${TEST_ROOT_DIR}/nested_test/proto)
  set(PROTO_FILES ${TEST_ROOT_DIR}/nested_test/proto/nested_test.proto
                  ${TEST_ROOT_DIR}/nested_test/proto/complex_types.proto)
endif()
message(STATUS "Proto files: ${PROTO_FILES}")
message(STATUS "Proto path: ${PROTO_PATH}")
# ============================================================
# Plugin API name
# ============================================================
if(ENABLE_UNARY_TEST)
  set(PLUGIN_API_NAME unary_test)
elseif(ENABLE_LOAD_ANOTHER_TEST)
  set(PLUGIN_API_NAME load_another)
elseif(ENABLE_ONEOF_TEST)
  set(PLUGIN_API_NAME oneof_test)
elseif(ENABLE_NESTED_TEST)
  set(PLUGIN_API_NAME nested_test)
endif()
message(STATUS "Plugin API library name: ${PLUGIN_API_NAME}")

# ============================================================
# Paths
# ============================================================
set(TMP_DIR ${CMAKE_CURRENT_BINARY_DIR}/tmp)

# ============================================================
# gRPC URL (test-specific)
# ============================================================
if(ENABLE_UNARY_TEST)
  set(GRPC_ENDPOINT "localhost:50001")
elseif(ENABLE_LOAD_ANOTHER_TEST)
  set(GRPC_ENDPOINT "localhost:50002")
elseif(ENABLE_ONEOF_TEST)
  set(GRPC_ENDPOINT "localhost:50003")
elseif(ENABLE_NESTED_TEST)
  set(GRPC_ENDPOINT "localhost:50004")
endif()
message(STATUS "gRPC endpoint: ${GRPC_ENDPOINT}")
# ============================================================
# Proto/gRPC generation
# ============================================================
set(PROTO_GEN_SRCS "")
set(PROTO_GEN_HDRS "")
set(GRPC_GEN_SRCS "")
set(GRPC_GEN_HDRS "")

foreach(proto_file IN LISTS PROTO_FILES)
  get_filename_component(proto_name ${proto_file} NAME_WE)
  list(APPEND PROTO_GEN_SRCS ${TMP_DIR}/${proto_name}.pb.cc)
  list(APPEND PROTO_GEN_HDRS ${TMP_DIR}/${proto_name}.pb.h)
  list(APPEND GRPC_GEN_SRCS ${TMP_DIR}/${proto_name}.grpc.pb.cc)
  list(APPEND GRPC_GEN_HDRS ${TMP_DIR}/${proto_name}.grpc.pb.h)
endforeach()

set(PLUGIN_GEN_SRCS
    ${TMP_DIR}/plugin_api_impl.cpp ${TMP_DIR}/rpc_client.cpp
    ${TMP_DIR}/rpc_client_factory.cpp
    ${TSURUGI_UDF_COMMON_DIR}/src/udf/descriptor_impl.cpp)
set(PLUGIN_GEN_HDRS ${TMP_DIR}/rpc_client.h)

# ============================================================
# Code generation command
# ============================================================
add_custom_command(
  OUTPUT ${PROTO_GEN_SRCS} ${PROTO_GEN_HDRS} ${GRPC_GEN_SRCS} ${GRPC_GEN_HDRS}
         ${PLUGIN_GEN_SRCS} ${PLUGIN_GEN_HDRS}
  COMMAND ${CMAKE_COMMAND} -E make_directory ${TMP_DIR}
  COMMAND
    ${Python3_EXECUTABLE} ${GENERATE_SCRIPT} --proto-file ${PROTO_FILES}
    --proto-path ${PROTO_PATH} --tmp ${TMP_DIR} --plugin_api_name
    ${PLUGIN_API_NAME} --grpc-endpoint ${GRPC_ENDPOINT} --out
    ${CMAKE_CURRENT_BINARY_DIR}
  DEPENDS ${GENERATE_SCRIPT} ${PROTO_FILES}
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/..
  COMMENT "Running generate.py for proto and plugin API generation")

# ============================================================
# Proto library
# ============================================================
add_library(proto_lib STATIC ${PROTO_GEN_SRCS} ${PROTO_GEN_HDRS}
                             ${GRPC_GEN_SRCS} ${GRPC_GEN_HDRS})
target_include_directories(proto_lib PUBLIC ${TMP_DIR} ${GRPC_INCLUDE_DIRS})
target_link_libraries(proto_lib PUBLIC ${GRPC_LIBRARIES} protobuf::libprotobuf)
set_target_properties(proto_lib PROPERTIES POSITION_INDEPENDENT_CODE ON)

# ============================================================
# Plugin API library
# ============================================================
add_library(${PLUGIN_API_NAME} SHARED ${PLUGIN_GEN_SRCS} ${PLUGIN_GEN_HDRS})
target_include_directories(
  ${PLUGIN_API_NAME} PRIVATE ${TSURUGI_UDF_COMMON_DIR}/include/udf ${TMP_DIR})
target_link_libraries(${PLUGIN_API_NAME} PRIVATE proto_lib ${GRPC_LIBRARIES}
                                                 protobuf::libprotobuf)

# ============================================================
# Clean target
# ============================================================
add_custom_target(
  clean_out
  COMMAND ${CMAKE_COMMAND} -E rm -rf "${TMP_DIR}"
  COMMENT "Removing tmp directory")
set_property(
  DIRECTORY
  APPEND
  PROPERTY ADDITIONAL_MAKE_CLEAN_FILES "${TMP_DIR}")

# ============================================================
# Test executables
# ============================================================
if(ENABLE_TESTS)

  if(ENABLE_UNARY_TEST)
    message(STATUS "Building unary_test")
    add_executable(rpc_server_unary_test
                   ${TEST_ROOT_DIR}/unary_test/server/rpc_server.cpp)
    target_include_directories(
      rpc_server_unary_test PRIVATE ${TMP_DIR}
                                    ${CMAKE_CURRENT_SOURCE_DIR}/include/udf)
    target_link_libraries(
      rpc_server_unary_test PRIVATE proto_lib ${GRPC_LIBRARIES}
                                    protobuf::libprotobuf)

    add_executable(
      rpc_client
      ${TEST_ROOT_DIR}/unary_test/client/client.cpp
      ${TMP_DIR}/rpc_client.cpp
      ${TMP_DIR}/rpc_client_factory.cpp
      ${TSURUGI_UDF_COMMON_DIR}/src/udf/generic_record_impl.cpp
      ${TSURUGI_UDF_COMMON_DIR}/src/udf/error_info.cpp
      ${TSURUGI_UDF_COMMON_DIR}/src/udf/descriptor_impl.cpp)
    target_include_directories(
      rpc_client PRIVATE ${TSURUGI_UDF_COMMON_DIR}/include/udf ${TMP_DIR})
    target_link_libraries(rpc_client PRIVATE proto_lib ${GRPC_LIBRARIES}
                                             protobuf::libprotobuf)
  endif()

  if(ENABLE_LOAD_ANOTHER_TEST)
    message(STATUS "Building load_another_test")
    add_executable(rpc_server_load_another
                   ${TEST_ROOT_DIR}/load_another/server/rpc_server.cpp)
    target_include_directories(
      rpc_server_load_another
      PRIVATE ${TMP_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/../include/udf)
    target_link_libraries(
      rpc_server_load_another PRIVATE proto_lib ${GRPC_LIBRARIES}
                                      protobuf::libprotobuf)
  endif()

  if(ENABLE_ONEOF_TEST)
    message(STATUS "Building oneof_test")
    add_executable(rpc_server_oneof_test
                   ${TEST_ROOT_DIR}/oneof_test/server/rpc_server.cpp)
    target_include_directories(
      rpc_server_oneof_test PRIVATE ${TMP_DIR}
                                    ${CMAKE_CURRENT_SOURCE_DIR}/include/udf)
    target_link_libraries(
      rpc_server_oneof_test PRIVATE proto_lib ${GRPC_LIBRARIES}
                                    protobuf::libprotobuf)

    add_executable(
      rpc_client_oneof
      ${TEST_ROOT_DIR}/oneof_test/client/client.cpp
      ${TMP_DIR}/rpc_client.cpp
      ${TMP_DIR}/rpc_client_factory.cpp
      ${TSURUGI_UDF_COMMON_DIR}/src/udf/generic_record_impl.cpp
      ${TSURUGI_UDF_COMMON_DIR}/src/udf/descriptor_impl.cpp
      ${TSURUGI_UDF_COMMON_DIR}/src/udf/error_info.cpp)
    target_include_directories(
      rpc_client_oneof PRIVATE ${TSURUGI_UDF_COMMON_DIR}/include/udf ${TMP_DIR})
    target_link_libraries(rpc_client_oneof PRIVATE proto_lib ${GRPC_LIBRARIES}
                                                   protobuf::libprotobuf)
  endif()

  if(ENABLE_NESTED_TEST)
    add_executable(rpc_server_nested_test
                   ${TEST_ROOT_DIR}/nested_test/server/rpc_server.cpp)
    target_include_directories(
      rpc_server_nested_test PRIVATE ${TMP_DIR}
                                     ${CMAKE_CURRENT_SOURCE_DIR}/include/udf)
    target_link_libraries(
      rpc_server_nested_test PRIVATE proto_lib ${GRPC_LIBRARIES}
                                     protobuf::libprotobuf)

    add_executable(
      rpc_client_nested_test
      ${TEST_ROOT_DIR}/nested_test/client/client.cpp
      ${TMP_DIR}/rpc_client.cpp
      ${TMP_DIR}/rpc_client_factory.cpp
      ${TSURUGI_UDF_COMMON_DIR}/src/udf/generic_record_impl.cpp
      ${TSURUGI_UDF_COMMON_DIR}/src/udf/descriptor_impl.cpp
      ${TSURUGI_UDF_COMMON_DIR}/src/udf/error_info.cpp)
    target_include_directories(
      rpc_client_nested_test PRIVATE ${TSURUGI_UDF_COMMON_DIR}/include/udf
                                     ${TMP_DIR})
    target_link_libraries(
      rpc_client_nested_test PRIVATE proto_lib ${GRPC_LIBRARIES}
                                     protobuf::libprotobuf)
  endif()
endif()
