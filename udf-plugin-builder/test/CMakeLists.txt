cmake_minimum_required(VERSION 3.14)
project(plugin_api_test)

find_package(Protobuf REQUIRED)
find_package(gRPC CONFIG REQUIRED)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Debug)

set(COMMON_LIBS
  gRPC::grpc++
  protobuf::libprotobuf
)

set(COMMON_INCLUDES
  ${CMAKE_CURRENT_SOURCE_DIR}/../../include
  ${CMAKE_CURRENT_SOURCE_DIR}/../include
  ${CMAKE_CURRENT_SOURCE_DIR}/../out
)

set(GENERATED_PROTO_SRCS
  ${CMAKE_CURRENT_SOURCE_DIR}/../out/sample.grpc.pb.cc
  ${CMAKE_CURRENT_SOURCE_DIR}/../out/sample.pb.cc
  ${CMAKE_CURRENT_SOURCE_DIR}/../out/complex_types.grpc.pb.cc
  ${CMAKE_CURRENT_SOURCE_DIR}/../out/complex_types.pb.cc
  ${CMAKE_CURRENT_SOURCE_DIR}/../out/primitive_types.grpc.pb.cc
  ${CMAKE_CURRENT_SOURCE_DIR}/../out/primitive_types.pb.cc
)

add_executable(
  inspect_plugin
  ${CMAKE_CURRENT_SOURCE_DIR}/inspect_plugin.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/udf/plugin_api.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/udf/udf_loader.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/udf/generic_record_impl.cpp
  )

target_include_directories(inspect_plugin PRIVATE ${COMMON_INCLUDES})
target_link_libraries(inspect_plugin PRIVATE ${COMMON_LIBS} dl)

add_executable(rpc_client
  ${CMAKE_CURRENT_SOURCE_DIR}/client/client.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../out/rpc_client.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../out/rpc_client_factory.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../../src/udf/generic_record_impl.cpp
  ${GENERATED_PROTO_SRCS}
)

target_include_directories(rpc_client PRIVATE ${COMMON_INCLUDES})
target_link_libraries(rpc_client PRIVATE ${COMMON_LIBS})

add_executable(rpc_server
  ${CMAKE_CURRENT_SOURCE_DIR}/server/rpc_server.cpp
  ${GENERATED_PROTO_SRCS}
)

target_include_directories(rpc_server PRIVATE ${COMMON_INCLUDES})
target_link_libraries(rpc_server PRIVATE ${COMMON_LIBS})