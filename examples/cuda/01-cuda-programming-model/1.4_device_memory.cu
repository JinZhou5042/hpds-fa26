/*
 * From this topic directory (see ../README.md for details).
 *
 * HTCondor (Notre Dame CRC): build on the front end, run on a GPU worker
 *   module load cuda/12.1
 *   make 1.4_device_memory
 *   ./1.4_device_memory
 *
 * Slurm (Purdue Anvil): build on the login node, run with sbatch
 *   module load modtree/gpu cuda/12.8.0
 *   make 1.4_device_memory
 *   sbatch ../common/anvil_gpu.slurm ./1.4_device_memory
 *
 * Section 1.4: Allocate, transfer, use, and free device memory
 *
 * The device-memory path is:
 *
 * 1. cudaMalloc allocates arrays in GPU global memory;
 * 2. an H2D cudaMemcpy sends input from the CPU to the GPU;
 * 3. the kernel reads the device input and writes the device output;
 * 4. a D2H cudaMemcpy returns output to the CPU;
 * 5. cudaFree releases each device allocation.
 *
 * The kernel reuses Section 1.3's indexing and boundary check. Section 1.5 adds
 * a second input array for vector addition.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <stdlib.h>
#include <stdio.h>

__global__ void double_elements(const int* input, int* output, int element_count) {
    const int global_id = blockIdx.x * blockDim.x + threadIdx.x;
    if (global_id < element_count) {
        output[global_id] = 2 * input[global_id];
    }
}

void double_elements_cpu(const int* input, int* output, int element_count) {
    for (int i = 0; i < element_count; ++i) {
        output[i] = 2 * input[i];
    }
}

int main() {
    int element_count = 6;
    int block_size = 4;
    int block_count = (element_count + block_size - 1) / block_size;
    int bytes = element_count * sizeof(int);

    /*
     * _h and _d are a common CUDA naming convention, not language syntax: _h
     * means host data and _d means a pointer containing a device address. The
     * suffixes improve readability; only CUDA API calls actually move data.
     */
    int input_h[6] = {3, 5, 8, 13, 21, 34};
    int output_h[6];
    int expected_h[6];

    double_elements_cpu(input_h, expected_h, element_count);
    
    int* input_d = nullptr;
    int* output_d = nullptr;

    // Phase 1: allocate two arrays in device global memory.
    check_cuda(cudaMalloc((void**)&input_d, bytes), "cudaMalloc input");
    check_cuda(cudaMalloc((void**)&output_d, bytes), "cudaMalloc output");

    // Phase 2: copy the input array from host memory to device memory.
    check_cuda(cudaMemcpy(input_d, input_h, bytes, cudaMemcpyHostToDevice), "copy input H2D");

    // Phase 3: launch enough threads to process every element.
    double_elements<<<block_count, block_size>>>(input_d, output_d, element_count);

    check_cuda(cudaGetLastError(), "launch double_elements");
    check_cuda(cudaDeviceSynchronize(), "execute double_elements");

    // Phase 4: copy the output array from device memory to host memory.
    check_cuda(cudaMemcpy(output_h, output_d, bytes, cudaMemcpyDeviceToHost), "copy output D2H");

    // Phase 5: release device memory after the CPU has received the result.
    check_cuda(cudaFree(input_d), "cudaFree input");
    check_cuda(cudaFree(output_d), "cudaFree output");

    bool correct = true;
    for (int i = 0; i < element_count; ++i) {
    	printf("input[%d]=%d -> output[%d] = %d\n",i,input_h[i],i,output_h[i]);
        correct = correct && output_h[i] == expected_h[i];
    }

    std::cout << "Verified " << element_count << " elements after allocate -> H2D -> kernel -> D2H -> free.\n";

    return correct ? EXIT_SUCCESS : EXIT_FAILURE;
}
