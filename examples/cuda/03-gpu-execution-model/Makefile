.PHONY: all clean

all: 3.1_device_properties 3.2_block_scheduling \
	3.3_block_synchronization 3.4_warps_and_divergence \
	3.5_occupancy overall

3.1_device_properties: 3.1_device_properties.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 3.1_device_properties.cu -o 3.1_device_properties

3.2_block_scheduling: 3.2_block_scheduling.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 3.2_block_scheduling.cu -o 3.2_block_scheduling

3.3_block_synchronization: 3.3_block_synchronization.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 3.3_block_synchronization.cu -o 3.3_block_synchronization

3.4_warps_and_divergence: 3.4_warps_and_divergence.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 3.4_warps_and_divergence.cu -o 3.4_warps_and_divergence

3.5_occupancy: 3.5_occupancy.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 3.5_occupancy.cu -o 3.5_occupancy

overall: overall.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 overall.cu -o overall

clean:
	rm -f 3.1_device_properties 3.2_block_scheduling \
		3.3_block_synchronization 3.4_warps_and_divergence \
		3.5_occupancy overall
