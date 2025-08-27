cmake_minimum_required(VERSION 3.10)
project(udf_app)

# Usage: cmake -S . -B build \ -DPROTO_PATH="proto" \
# -DPROTO_FILES="proto/sample.proto;proto/extra.proto" \
# -DPLUGIN_API_NAME="my_udf"
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
set(OUT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/out)

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
  COMMAND ${CMAKE_COMMAND} -E echo "Generating code from proto and API..."
  COMMAND ${Python3_EXECUTABLE} ${GENERATE_SCRIPT} --proto_path ${PROTO_PATH}
          --proto_file ${PROTO_FILES} --out ${OUT_DIR}
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
