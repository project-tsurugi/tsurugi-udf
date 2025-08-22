cmake_minimum_required(VERSION 3.14)
project(plugin_api_test)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/../../cmake")
find_package(Protobuf REQUIRED)
find_package(gRPC REQUIRED)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Debug)

set(COMMON_LIBS ${GRPC_LIBRARIES} protobuf::libprotobuf)

set(COMMON_INCLUDES
    ${CMAKE_CURRENT_SOURCE_DIR}/../../include
    ${CMAKE_CURRENT_SOURCE_DIR}/include ${CMAKE_CURRENT_SOURCE_DIR}/../include
    ${CMAKE_CURRENT_SOURCE_DIR}/../out)

link_directories(${CMAKE_CURRENT_SOURCE_DIR}/../build)
find_library(PROTO_LIB proto_lib PATHS ${CMAKE_CURRENT_SOURCE_DIR}/../build)
if(NOT PROTO_LIB)
  message(FATAL_ERROR "proto_lib not found")
endif()

# inspect_plugin
add_executable(
  inspect_plugin
  ${CMAKE_CURRENT_SOURCE_DIR}/src/inspect_plugin.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/src/rpc_tasks.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/src/task_manager.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/udf/plugin_api.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/udf/udf_loader.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/udf/generic_record_impl.cpp)

target_include_directories(inspect_plugin PRIVATE ${COMMON_INCLUDES})
target_link_libraries(inspect_plugin PRIVATE ${COMMON_LIBS} dl proto_lib)

# rpc_client
add_executable(
  rpc_client
  ${CMAKE_CURRENT_SOURCE_DIR}/client/client.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../out/rpc_client.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../out/rpc_client_factory.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/udf/generic_record_impl.cpp)

target_include_directories(rpc_client PRIVATE ${COMMON_INCLUDES})
target_link_libraries(rpc_client PRIVATE ${COMMON_LIBS} proto_lib)

# rpc_server
add_executable(rpc_server ${CMAKE_CURRENT_SOURCE_DIR}/server/rpc_server.cpp)

target_include_directories(rpc_server PRIVATE ${COMMON_INCLUDES})
target_link_libraries(rpc_server PRIVATE ${COMMON_LIBS} proto_lib)
