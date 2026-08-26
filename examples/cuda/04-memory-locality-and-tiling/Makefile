.PHONY: all clean

all: 4.1_memory_spaces 4.2_arithmetic_intensity 4.3_shared_memory \
	4.4_tiled_matrix_multiplication 4.5_boundary_safe_tiling \
	4.6_dynamic_shared_occupancy overall

4.1_memory_spaces: 4.1_memory_spaces.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 4.1_memory_spaces.cu -o 4.1_memory_spaces

4.2_arithmetic_intensity: 4.2_arithmetic_intensity.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 4.2_arithmetic_intensity.cu -o 4.2_arithmetic_intensity

4.3_shared_memory: 4.3_shared_memory.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 4.3_shared_memory.cu -o 4.3_shared_memory

4.4_tiled_matrix_multiplication: 4.4_tiled_matrix_multiplication.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 4.4_tiled_matrix_multiplication.cu -o 4.4_tiled_matrix_multiplication

4.5_boundary_safe_tiling: 4.5_boundary_safe_tiling.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 4.5_boundary_safe_tiling.cu -o 4.5_boundary_safe_tiling

4.6_dynamic_shared_occupancy: 4.6_dynamic_shared_occupancy.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 4.6_dynamic_shared_occupancy.cu -o 4.6_dynamic_shared_occupancy

overall: overall.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 overall.cu -o overall

clean:
	rm -f 4.1_memory_spaces 4.2_arithmetic_intensity 4.3_shared_memory \
		4.4_tiled_matrix_multiplication 4.5_boundary_safe_tiling \
		4.6_dynamic_shared_occupancy overall
