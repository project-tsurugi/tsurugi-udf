cmake_minimum_required(VERSION 3.10)
project(udf_app)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(GENERATE_SCRIPT ${CMAKE_CURRENT_SOURCE_DIR}/generate.py)
set(GENERATED_CPP ${CMAKE_CURRENT_SOURCE_DIR}/out/plugin_api_impl.cpp)

add_custom_command(
    OUTPUT ${GENERATED_CPP}
    COMMAND ${CMAKE_COMMAND} -E echo "Generating plugin_api_impl.cpp..."
    COMMAND ${Python3_EXECUTABLE} ${GENERATE_SCRIPT}
    DEPENDS ${GENERATE_SCRIPT}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Running generate.py"
)

add_custom_target(generate_plugin_api_cpp
    DEPENDS ${GENERATED_CPP}
)

add_library(plugin_api SHARED
    ${GENERATED_CPP}
)

target_include_directories(plugin_api PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../include
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

add_dependencies(plugin_api generate_plugin_api_cpp)

find_package(Python3 REQUIRED)
