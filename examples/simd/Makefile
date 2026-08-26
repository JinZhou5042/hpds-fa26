
PROGRAMS=simple simple-opt simd-support intrinsics structure-of-arrays array-of-structures

all: ${PROGRAMS}

clean:
	rm -f ${PROGRAMS}

simple: simple.c
	g++ simple.c -o simple -O0

simple-opt: simple.c
	g++ simple.c -o simple-opt -mavx -O3

simd-support: simd-support.c
	g++ simd-support.c -o simd-support

intrinsics: intrinsics.c
	g++ intrinsics.c -o intrinsics -mavx -O3

structure-of-arrays: structure-of-arrays.c
	g++ structure-of-arrays.c -o structure-of-arrays -O3

array-of-structures: array-of-structures.c
	g++ array-of-structures.c -o array-of-structures -O3

# Some things to try:
#     time ./simple
#     time ./simple-opt
#     objdump --disassemble simple-opt

# Try compiling with various options:
#     -msse -msse2 -msse4.2 -mavx -mavx2 -mavx512f
#     -fopt-info-vec-all -fopt-info-vec-missed
