cmake_minimum_required(VERSION 3.14)
project(plugin_api_test)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Debug)
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/../../include
    ${CMAKE_CURRENT_SOURCE_DIR}/../include
)

add_executable(inspect_plugin 
${CMAKE_CURRENT_SOURCE_DIR}/inspect_plugin.cpp 
${CMAKE_CURRENT_SOURCE_DIR}/../../src/udf/plugin_api.cpp
${CMAKE_CURRENT_SOURCE_DIR}/../../src/udf/udf_loader.cpp
)

target_link_libraries(inspect_plugin dl)
