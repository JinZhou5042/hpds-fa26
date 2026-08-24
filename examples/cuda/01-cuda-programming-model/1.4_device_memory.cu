/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 1.4_device_memory
 *   make condor_run build/1.4_device_memory
 *   make condor_submit build/1.4_device_memory
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

#include <array>
#include <cstdlib>
#include <iostream>


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
    constexpr int element_count = 6;
    constexpr int block_size = 4;
    constexpr int block_count = (element_count + block_size - 1) / block_size;
    constexpr std::size_t bytes = element_count * sizeof(int);

    /*
     * _h and _d are a common CUDA naming convention, not language syntax: _h
     * means host data and _d means a pointer containing a device address. The
     * suffixes improve readability; only CUDA API calls actually move data.
     */
    const std::array<int, element_count> input_h = {3, 5, 8, 13, 21, 34};
    std::array<int, element_count> output_h{};
    std::array<int, element_count> expected_h{};

    double_elements_cpu(input_h.data(), expected_h.data(), element_count);

    int* input_d = nullptr;
    int* output_d = nullptr;

    // Phase 1: allocate two arrays in device global memory.
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&input_d), bytes), "cudaMalloc input");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&output_d), bytes), "cudaMalloc output");

    // Phase 2: copy the input array from host memory to device memory.
    check_cuda(cudaMemcpy(input_d, input_h.data(), bytes, cudaMemcpyHostToDevice), "copy input H2D");

    // Phase 3: launch enough threads to process every element.
    double_elements<<<block_count, block_size>>>(input_d, output_d, element_count);
    check_cuda(cudaGetLastError(), "launch double_elements");
    check_cuda(cudaDeviceSynchronize(), "execute double_elements");

    // Phase 4: copy the output array from device memory to host memory.
    check_cuda(cudaMemcpy(output_h.data(), output_d, bytes, cudaMemcpyDeviceToHost), "copy output D2H");

    // Phase 5: release device memory after the CPU has received the result.
    check_cuda(cudaFree(input_d), "cudaFree input");
    check_cuda(cudaFree(output_d), "cudaFree output");

    bool correct = true;
    for (int i = 0; i < element_count; ++i) {
        std::cout << "input[" << i << "]=" << input_h[i] << " -> output[" << i << "]=" << output_h[i] << '\n';
        correct = correct && output_h[i] == expected_h[i];
    }

    std::cout << "Verified " << element_count << " elements after allocate -> H2D -> kernel -> D2H -> free.\n";

    return correct ? EXIT_SUCCESS : EXIT_FAILURE;
}
