## Libtorch (C++) test

Solution of the linear advection equation on a curvilinar O-type grid. Equivalent codes are given in C++ and Python.

1. Download libtorch binary (or compile it)
2. Build the test program:
```
mkdir build && cd build
cmake -DCMAKE_PREFIX_PATH=/absolute/path/to/libtorch ..
make
```
3. Run: `./conv_FD`