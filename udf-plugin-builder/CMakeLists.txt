cmake_minimum_required(VERSION 3.10)
project(udf_app)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Protobuf REQUIRED)
find_package(gRPC CONFIG REQUIRED)
find_package(Python3 REQUIRED)

set(GENERATE_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/generate.py)
set(GENERATED_CPP_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/out/plugin_api_impl.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/out/rpc_client.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/out/rpc_client_factory.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/out/sample.grpc.pb.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/out/sample.pb.cc)

set(GENERATED_HEADER_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/out/sample.grpc.pb.h
    ${CMAKE_CURRENT_SOURCE_DIR}/out/sample.pb.h
    ${CMAKE_CURRENT_SOURCE_DIR}/out/rpc_client.h)

add_custom_command(
  OUTPUT ${GENERATED_CPP_FILES} ${GENERATED_HEADER_FILES}
  COMMAND ${CMAKE_COMMAND} -E echo "Generating plugin_api_impl.cpp..."
  COMMAND ${Python3_EXECUTABLE} ${GENERATE_SCRIPT}
  DEPENDS ${GENERATE_SCRIPT}
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
  COMMENT "Running generate.py")

add_custom_target(generate_plugin_api_cpp DEPENDS ${GENERATED_CPP_FILES}
                                                  ${GENERATED_HEADER_FILES})

add_library(plugin_api SHARED ${GENERATED_CPP_FILES})

target_include_directories(
  plugin_api
  PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../include
          ${CMAKE_CURRENT_SOURCE_DIR}/include ${CMAKE_CURRENT_SOURCE_DIR}/out)

add_dependencies(plugin_api generate_plugin_api_cpp)

target_link_libraries(plugin_api gRPC::grpc++ protobuf::libprotobuf)

add_custom_target(
  clean_out
  COMMAND ${CMAKE_COMMAND} -E rm -rf "${CMAKE_CURRENT_SOURCE_DIR}/out"
  COMMENT "Removing out directory")
set_property(
  DIRECTORY
  APPEND
  PROPERTY ADDITIONAL_MAKE_CLEAN_FILES "${CMAKE_CURRENT_SOURCE_DIR}/out")
