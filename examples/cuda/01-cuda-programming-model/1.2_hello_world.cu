/*
 * From this topic directory (see ../README.md for details).
 *
 * HTCondor (Notre Dame CRC): build on the front end, run on a GPU worker
 *   module load cuda/12.1
 *   make 1.2_kernel_launch
 *   ./1.2_kernel_launch
 *
 * Slurm (Purdue Anvil): build on the login node, run with sbatch
 *   module load modtree/gpu cuda/12.8.0
 *   make 1.2_kernel_launch
 *   sbatch ../common/anvil_gpu.slurm ./1.2_kernel_launch
 *
 * Section 1.2: Launch one block of GPU threads
 *
 * This first kernel launches one block of four threads. __global__ marks the
 * kernel, <<<1, 4>>> sets the launch shape, and threadIdx.x identifies a thread
 * inside the block. Arrays and device memory come later.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <stdio.h>
#include <stdlib.h>

/*
 * __global__ means that main launches this function from the CPU and its body
 * runs on the GPU. Every launched thread executes the same function. This is
 * SPMD: one program operates on multiple pieces of data. SPMD is a programming
 * model, whereas SIMD is a hardware execution style. SPMD threads run the same
 * program but do not have to execute the same instruction at the same moment.
 */
__global__ void show_local_thread_id() {
    // threadIdx.x is 0, 1, 2, or 3 for this four-thread block.
    printf("Hello from local thread %u\n", threadIdx.x);
}

int main() {
    int block_count = 1;
    int threads_per_block = 4;

    printf("Launching one block with four threads\n");

    /*
     * The first launch value is the number of blocks. The second is the number
     * of threads in each block.
     */
    show_local_thread_id<<<block_count, threads_per_block>>>();

    // Check the launch, then wait for the GPU and flush device printf output.
    check_cuda(cudaGetLastError(), "launch show_local_thread_id");
    check_cuda(cudaDeviceSynchronize(), "execute show_local_thread_id");
}
