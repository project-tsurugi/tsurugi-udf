cmake_minimum_required(VERSION 3.10)
project(udf_app)

# Usage: cmake -S . -B build \ -DPROTO_PATH="proto" \
# -DPROTO_FILES="proto/sample.proto;proto/complex_types.proto;proto/primitive_types.proto"
# \ -DPLUGIN_API_NAME="my_udf"
#
# Options: PROTO_PATH        Path to .proto files directory (default: proto)
# PROTO_FILES       List of .proto files to compile (default: sample.proto,
# complex_types.proto, primitive_types.proto) PLUGIN_API_NAME   Name of the
# generated plugin_api library target (default: plugin_api)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/../cmake")
find_package(Protobuf REQUIRED)
find_package(gRPC REQUIRED)
find_package(Python3 REQUIRED)
find_program(PROTOC_EXECUTABLE protoc)
if(NOT PROTOC_EXECUTABLE)
  message(FATAL_ERROR "protoc not found!")
endif()
find_program(GRPC_CPP_PLUGIN_EXECUTABLE grpc_cpp_plugin)
if(NOT GRPC_CPP_PLUGIN_EXECUTABLE)
  message(FATAL_ERROR "grpc_cpp_plugin not found!")
endif()

set(GENERATE_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/generate.py)

# ====== build type ======
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE
      Debug
      CACHE STRING "Choose the build type")
endif()
set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release"
                                             "RelWithDebInfo" "MinSizeRel")

# ====== proto files ======
set(DEFAULT_PROTO_FILES proto/sample.proto proto/complex_types.proto
                        proto/primitive_types.proto)
set(PROTO_FILES
    ${DEFAULT_PROTO_FILES}
    CACHE STRING "List of proto files to generate")
string(REPLACE ";" " " PROTO_FILES_STR "${PROTO_FILES}")

set(DEFAULT_PROTO_PATH proto)
set(PROTO_PATH
    ${DEFAULT_PROTO_PATH}
    CACHE STRING "Directories containing proto files")

# ====== library name ======
set(DEFAULT_PLUGIN_API_NAME plugin_api)
set(PLUGIN_API_NAME
    ${DEFAULT_PLUGIN_API_NAME}
    CACHE STRING "Name of the plugin_api library target (default: plugin_api)")
message(STATUS "Plugin API library name: ${PLUGIN_API_NAME}")

# ====== output dir ======
set(DEFAULT_OUT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/out)
set(OUT_DIR
    ${DEFAULT_OUT_DIR}
    CACHE PATH
          "Output directory for generated code (default: ${DEFAULT_OUT_DIR})")

# ====== list of generated files ======
set(PROTO_GEN_SRCS "")
set(PROTO_GEN_HDRS "")
set(GRPC_GEN_SRCS "")
set(GRPC_GEN_HDRS "")

foreach(proto_file IN LISTS PROTO_FILES)
  get_filename_component(proto_name ${proto_file} NAME_WE)
  list(APPEND PROTO_GEN_SRCS ${OUT_DIR}/${proto_name}.pb.cc)
  list(APPEND PROTO_GEN_HDRS ${OUT_DIR}/${proto_name}.pb.h)
  list(APPEND GRPC_GEN_SRCS ${OUT_DIR}/${proto_name}.grpc.pb.cc)
  list(APPEND GRPC_GEN_HDRS ${OUT_DIR}/${proto_name}.grpc.pb.h)
endforeach()

set(PLUGIN_GEN_SRCS ${OUT_DIR}/plugin_api_impl.cpp ${OUT_DIR}/rpc_client.cpp
                    ${OUT_DIR}/rpc_client_factory.cpp)
set(PLUGIN_GEN_HDRS ${OUT_DIR}/rpc_client.h)

# ====== code generation rules ======
add_custom_command(
  OUTPUT ${PROTO_GEN_SRCS} ${PROTO_GEN_HDRS} ${GRPC_GEN_SRCS} ${GRPC_GEN_HDRS}
         ${PLUGIN_GEN_SRCS} ${PLUGIN_GEN_HDRS}
  COMMAND ${CMAKE_COMMAND} -E echo "Generating out directory..."
  COMMAND ${CMAKE_COMMAND} -E make_directory ${OUT_DIR}
  COMMAND ${CMAKE_COMMAND} -E echo
          "Generating C++ and gRPC code from proto files..."
  COMMAND
    ${PROTOC_EXECUTABLE} -I${PROTO_PATH} --cpp_out=${OUT_DIR}
    --grpc_out=${OUT_DIR} --plugin=protoc-gen-grpc=${GRPC_CPP_PLUGIN_EXECUTABLE}
    --descriptor_set_out=${OUT_DIR}/descriptor.pb --include_imports
    ${PROTO_FILES}
  COMMAND ${CMAKE_COMMAND} -E echo "Generating code from proto and API..."
  COMMAND ${Python3_EXECUTABLE} ${GENERATE_SCRIPT} --proto_file ${PROTO_FILES}
          --out ${OUT_DIR}
  DEPENDS ${GENERATE_SCRIPT} ${PROTO_FILES}
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
  COMMENT "Running generate.py")

# ====== proto library ======
add_library(proto_lib SHARED ${PROTO_GEN_SRCS} ${PROTO_GEN_HDRS}
                             ${GRPC_GEN_SRCS} ${GRPC_GEN_HDRS})
target_include_directories(proto_lib PUBLIC ${OUT_DIR} ${GRPC_INCLUDE_DIRS})
target_link_libraries(proto_lib PUBLIC ${GRPC_LIBRARIES} protobuf::libprotobuf)
set_target_properties(proto_lib PROPERTIES POSITION_INDEPENDENT_CODE ON)

# ====== output library ======
add_library(${PLUGIN_API_NAME} SHARED ${PLUGIN_GEN_SRCS} ${PLUGIN_GEN_HDRS})
target_include_directories(
  ${PLUGIN_API_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../include ${OUT_DIR})
target_link_libraries(${PLUGIN_API_NAME} PRIVATE proto_lib ${GRPC_LIBRARIES}
                                                 protobuf::libprotobuf)

# ====== clean target ======
add_custom_target(
  clean_out
  COMMAND ${CMAKE_COMMAND} -E rm -rf "${OUT_DIR}"
  COMMENT "Removing out directory")
set_property(
  DIRECTORY
  APPEND
  PROPERTY ADDITIONAL_MAKE_CLEAN_FILES "${OUT_DIR}")
# ====== test options ======
option(ENABLE_TESTS "Build tests" OFF)
if(ENABLE_TESTS)
  option(ENABLE_UNARY_TEST "Build unary_test" OFF)

  # cmake .. -DPROTO_PATH="test/unary_test/proto"
  # -DPROTO_FILES="test/unary_test/proto/test_all.proto" -DENABLE_TESTS=ON
  # -DENABLE_UNARY_TEST=ON
  if(ENABLE_UNARY_TEST)
    message(STATUS "Building unary_test")
    # ====== rpc server/client ======
    add_executable(
      rpc_server
      ${CMAKE_CURRENT_SOURCE_DIR}/test/unary_test/server/rpc_server.cpp)
    target_include_directories(
      rpc_server PRIVATE ${OUT_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/include)
    target_link_libraries(rpc_server PRIVATE proto_lib ${GRPC_LIBRARIES}
                                             protobuf::libprotobuf)
    add_executable(
      rpc_client
      ${CMAKE_CURRENT_SOURCE_DIR}/test/unary_test/client/client.cpp
      ${OUT_DIR}/rpc_client.cpp ${OUT_DIR}/rpc_client_factory.cpp
      ${CMAKE_CURRENT_SOURCE_DIR}/../src/udf/generic_record_impl.cpp)
    target_include_directories(
      ${PLUGIN_API_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../include
                                 ${OUT_DIR})
    target_include_directories(rpc_client
                               PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../include)
    target_link_libraries(rpc_client PRIVATE proto_lib ${GRPC_LIBRARIES}
                                             protobuf::libprotobuf)
  endif()
endif()
