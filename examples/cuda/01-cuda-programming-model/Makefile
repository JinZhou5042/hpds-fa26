.PHONY: all clean

all: 1.1_cpu_vector_add 1.2_hello_world 1.3_global_indices \
	1.4_device_memory 1.5_vector_add 1.6_correctness \
	1.7_function_qualifiers overall \
	1.8_unified_memory

1.1_cpu_vector_add: 1.1_cpu_vector_add.cpp
	g++ -O2 -std=c++17 -Wall -Wextra 1.1_cpu_vector_add.cpp -o 1.1_cpu_vector_add

1.2_hello_world: 1.2_hello_world.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 1.2_hello_world.cu -o 1.2_hello_world

1.3_global_indices: 1.3_global_indices.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 1.3_global_indices.cu -o 1.3_global_indices

1.4_device_memory: 1.4_device_memory.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 1.4_device_memory.cu -o 1.4_device_memory

1.5_vector_add: 1.5_vector_add.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 1.5_vector_add.cu -o 1.5_vector_add

1.6_correctness: 1.6_correctness.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 1.6_correctness.cu -o 1.6_correctness

1.7_function_qualifiers: 1.7_function_qualifiers.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 1.7_function_qualifiers.cu -o 1.7_function_qualifiers

1.8_unified_memory: 1.8_unified_memory.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 1.8_unified_memory.cu -o 1.8_unified_memory

overall: overall.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 overall.cu -o overall

clean:
	rm -f 1.1_cpu_vector_add 1.2_kernel_launch 1.3_global_indices \
		1.4_device_memory 1.5_vector_add 1.6_correctness \
		1.7_function_qualifiers overall
