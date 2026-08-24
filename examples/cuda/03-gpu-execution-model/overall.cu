/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make overall
 *   make condor_run build/overall
 *   make condor_submit build/overall
 *
 * Overall program: Architecture-aware block-size experiment
 *
 * The program queries the device, then sweeps block sizes while it:
 *
 * - query SM, warp, thread, register, and shared-memory limits;
 * - partition each block into warps;
 * - use a block barrier for a shared producer/consumer phase;
 * - calculate resource-limited theoretical occupancy;
 * - sweep block sizes and measure steady-state kernel time;
 * - validate every configuration rather than assuming faster means correct.
 *
 * Occupancy and measured time are reported separately.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>


__global__ void architecture_kernel(const float* input, float* output, int n) {
    extern __shared__ float tile[];
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    const int lane_in_block = threadIdx.x;

    // Every thread participates; rounded-up threads contribute neutral zero.
    tile[lane_in_block] = i < n ? input[i] : 0.0f;

    // Read-after-write barrier: neighbors must finish producing tile values.
    __syncthreads();

    if (i < n) {
        const int neighbor = lane_in_block == 0 ? 0 : lane_in_block - 1;
        output[i] = input[i] + tile[neighbor];
    }
}


int main() {
    const int n = 1'000'003;
    const int repetitions = 20;
    const int candidates[] = {32, 64, 128, 256, 512, 1024};
    const std::size_t bytes = static_cast<std::size_t>(n) * sizeof(float);

    int device = 0;
    CUDA_CHECK(cudaGetDevice(&device));
    cudaDeviceProp p{};
    CUDA_CHECK(cudaGetDeviceProperties(&p, device));
    cudaFuncAttributes attributes{};
    CUDA_CHECK(cudaFuncGetAttributes(&attributes, architecture_kernel));

    std::cout << "Device: " << p.name << '\n' << "SMs: " << p.multiProcessorCount << ", warp size: " << p.warpSize << ", max threads/SM: " << p.maxThreadsPerMultiProcessor << '\n'
              << "Kernel registers/thread: " << attributes.numRegs << "\n\n";

    std::vector<float> input_h(n);
    std::vector<float> output_h(n);
    for (int i = 0; i < n; ++i) {
        input_h[i] = static_cast<float>(i % 1009) * 0.001f;
    }

    float* input_d = nullptr;
    float* output_d = nullptr;
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&input_d), bytes));
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&output_d), bytes));
    CUDA_CHECK(cudaMemcpy(input_d, input_h.data(), bytes, cudaMemcpyHostToDevice));

    std::cout << std::left << std::setw(8) << "Block" << std::setw(8) << "Warps" << std::setw(12) << "Blocks/SM" << std::setw(12) << "Occupancy" << "Kernel ms\n";

    bool all_correct = true;
    for (const int block_size : candidates) {
        if (block_size > p.maxThreadsPerBlock) {
            continue;
        }
        const int grid_size = (n + block_size - 1) / block_size;
        const std::size_t shared_bytes = block_size * sizeof(float);

        int blocks_per_sm = 0;
        CUDA_CHECK(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&blocks_per_sm, architecture_kernel, block_size, shared_bytes));
        const int warps_per_block = (block_size + p.warpSize - 1) / p.warpSize;
        const int max_warps = p.maxThreadsPerMultiProcessor / p.warpSize;
        const double occupancy = static_cast<double>(blocks_per_sm * warps_per_block) / max_warps;

        architecture_kernel<<<grid_size, block_size, shared_bytes>>>(input_d, output_d, n);
        CUDA_CHECK(cudaDeviceSynchronize()); // warm-up

        const float total_ms = time_cuda_ms([&] {
            for (int repetition = 0; repetition < repetitions; ++repetition) {
                architecture_kernel<<<grid_size, block_size, shared_bytes>>>(input_d, output_d, n);
            }
            CUDA_CHECK(cudaGetLastError());
        });
        const float kernel_ms = total_ms / repetitions;
        CUDA_CHECK(cudaMemcpy(output_h.data(), output_d, bytes, cudaMemcpyDeviceToHost));

        bool correct = true;
        for (int i = 0; i < n; ++i) {
            const int lane = i % block_size;
            const int neighbor_i = lane == 0 ? i : i - 1;
            const float expected = input_h[i] + input_h[neighbor_i];
            correct = correct && std::fabs(output_h[i] - expected) <= 1.0e-6f;
        }
        all_correct = all_correct && correct;

        std::cout << std::left << std::fixed << std::setprecision(3) << std::setw(8) << block_size << std::setw(8) << warps_per_block << std::setw(12) << blocks_per_sm
                  << std::setw(12) << 100.0 * occupancy << kernel_ms << '\n';
    }

    CUDA_CHECK(cudaFree(input_d));
    CUDA_CHECK(cudaFree(output_d));
    std::cout << "\nOccupancy estimates resident warp capacity; measured time decides performance.\n";
    return all_correct ? EXIT_SUCCESS : EXIT_FAILURE;
}
