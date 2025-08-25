cmake_minimum_required(VERSION 3.10)
project(udf_app)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/../cmake")
find_package(Protobuf REQUIRED)
find_package(gRPC REQUIRED)
find_package(Python3 REQUIRED)

set(GENERATE_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/generate.py)

set(PROTO_GEN_SRCS
    ${CMAKE_CURRENT_SOURCE_DIR}/out/sample.pb.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/out/complex_types.pb.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/out/primitive_types.pb.cc)
set(PROTO_GEN_HDRS
    ${CMAKE_CURRENT_SOURCE_DIR}/out/sample.pb.h
    ${CMAKE_CURRENT_SOURCE_DIR}/out/complex_types.pb.h
    ${CMAKE_CURRENT_SOURCE_DIR}/out/primitive_types.pb.h)
set(GRPC_GEN_SRCS
    ${CMAKE_CURRENT_SOURCE_DIR}/out/sample.grpc.pb.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/out/complex_types.grpc.pb.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/out/primitive_types.grpc.pb.cc)
set(GRPC_GEN_HDRS
    ${CMAKE_CURRENT_SOURCE_DIR}/out/sample.grpc.pb.h
    ${CMAKE_CURRENT_SOURCE_DIR}/out/complex_types.grpc.pb.h
    ${CMAKE_CURRENT_SOURCE_DIR}/out/primitive_types.grpc.pb.h)

set(PLUGIN_GEN_SRCS
    ${CMAKE_CURRENT_SOURCE_DIR}/out/plugin_api_impl.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/out/rpc_client.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/out/rpc_client_factory.cpp)
set(PLUGIN_GEN_HDRS ${CMAKE_CURRENT_SOURCE_DIR}/out/rpc_client.h)

add_custom_command(
  OUTPUT ${PROTO_GEN_SRCS} ${PROTO_GEN_HDRS} ${GRPC_GEN_SRCS} ${GRPC_GEN_HDRS}
         ${PLUGIN_GEN_SRCS} ${PLUGIN_GEN_HDRS}
  COMMAND ${CMAKE_COMMAND} -E echo "Generating code from proto and API..."
  COMMAND ${Python3_EXECUTABLE} ${GENERATE_SCRIPT}
  DEPENDS ${GENERATE_SCRIPT}
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
  COMMENT "Running generate.py")

add_custom_target(
  generate_plugin_api_cpp
  DEPENDS ${PROTO_GEN_SRCS} ${PROTO_GEN_HDRS} ${GRPC_GEN_SRCS} ${GRPC_GEN_HDRS}
          ${PLUGIN_GEN_SRCS} ${PLUGIN_GEN_HDRS})

add_library(proto_lib SHARED ${PROTO_GEN_SRCS} ${PROTO_GEN_HDRS}
                             ${GRPC_GEN_SRCS} ${GRPC_GEN_HDRS})
target_include_directories(proto_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/out
                                            ${GRPC_INCLUDE_DIRS})
target_link_libraries(proto_lib PUBLIC ${GRPC_LIBRARIES} protobuf::libprotobuf)
set_target_properties(proto_lib PROPERTIES POSITION_INDEPENDENT_CODE ON)
add_dependencies(proto_lib generate_plugin_api_cpp)

add_library(plugin_api SHARED ${PLUGIN_GEN_SRCS} ${PLUGIN_GEN_HDRS})
target_include_directories(
  plugin_api PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../include
                     ${CMAKE_CURRENT_SOURCE_DIR}/out)
target_link_libraries(plugin_api PRIVATE proto_lib ${GRPC_LIBRARIES}
                                         protobuf::libprotobuf)
add_dependencies(plugin_api generate_plugin_api_cpp)

add_custom_target(
  clean_out
  COMMAND ${CMAKE_COMMAND} -E rm -rf "${CMAKE_CURRENT_SOURCE_DIR}/out"
  COMMENT "Removing out directory")
set_property(
  DIRECTORY
  APPEND
  PROPERTY ADDITIONAL_MAKE_CLEAN_FILES "${CMAKE_CURRENT_SOURCE_DIR}/out")
