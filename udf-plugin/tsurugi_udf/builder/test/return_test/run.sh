#!/bin/bash -x

rm -rf build
mkdir -p build
cd build
rm -rf *
cmake ../../../udf_plugin_builder/cmake/ -DENABLE_TESTS=ON -DENABLE_RETURN_TEST=ON
make
