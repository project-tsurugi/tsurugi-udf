#!/bin/bash

mkdir -p build
cd build
make clean_out 
rm -rf * 
cmake ../../../ -DENABLE_TESTS=ON -DENABLE_ONEOF_TEST=ON
make
