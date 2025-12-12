#!/bin/bash

rm -rf build
mkdir -p build
cd build
make clean_out
rm -rf *
cmake ../../../udf_plugin_builder/cmake/ -DENABLE_TESTS=ON -DENABLE_LOAD_ANOTHER_TEST=ON
make
