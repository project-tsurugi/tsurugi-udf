#!/bin/bash

mkdir -p build
cd build
make clean_out 
rm -rf * 
cmake ../../../ -DENABLE_TESTS=ON -DENABLE_LOAD_ANOTHER_TEST=ON
make
