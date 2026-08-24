/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 1.3_global_indices
 *   make condor_run build/1.3_global_indices
 *   make condor_submit build/1.3_global_indices
 *
 * Section 1.3: Map multiple blocks to element indices
 *
 * threadIdx.x restarts at zero in each block, so a grid-wide index also needs
 * blockIdx.x and blockDim.x:
 *
 *     blockIdx.x * blockDim.x + threadIdx.x
 *
 * Ceiling division may launch extra threads. The boundary check keeps those
 * threads from touching data. This example is one-dimensional and uses only
 * the x fields of CUDA's built-in index variables.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <cstdio>
#include <cstdlib>
#include <iostream>


__global__ void show_element_mapping(int element_count) {
    const int element_index = blockIdx.x * blockDim.x + threadIdx.x;

    if (element_index < element_count) {
        printf("block %u, thread %u -> element %d\n", blockIdx.x, threadIdx.x, element_index);
    } else {
        printf("block %u, thread %u -> no element (extra thread)\n", blockIdx.x, threadIdx.x);
    }
}

int main() {
    constexpr int element_count = 10;
    constexpr int block_size = 4;
    constexpr int block_count = (element_count + block_size - 1) / block_size;

    std::cout << "Elements: " << element_count << '\n' << "Launch: " << block_count << " blocks x " << block_size << " threads = " << block_count * block_size << " threads\n";

    show_element_mapping<<<block_count, block_size>>>(element_count);
    check_cuda(cudaGetLastError(), "launch show_element_mapping");
    check_cuda(cudaDeviceSynchronize(), "execute show_element_mapping");

    /*
     * All 12 threads print, but only 10 threads select elements 0 through 9.
     * The line order may change because GPU block execution order is not fixed.
     */
}
