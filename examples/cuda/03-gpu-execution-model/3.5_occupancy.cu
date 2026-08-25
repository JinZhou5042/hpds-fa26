/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 3.5_occupancy
 *   ./3.5_occupancy
 *
 * Section 3.5: Resource partitioning, residency, and occupancy
 *
 * Occupancy = active warps per SM / maximum warps per SM.
 *
 * Active blocks are limited simultaneously by:
 *
 * - maximum blocks per SM;
 * - maximum threads/warps per SM;
 * - registers required by each block;
 * - shared memory required by each block.
 *
 * More resident warps give the scheduler more alternatives while other warps
 * wait for memory or pipeline latency. This is latency hiding. Occupancy is not
 * an execution-efficiency percentage and 100% is not always required for speed.
 * The table puts theoretical occupancy beside measured time. Occupancy shows
 * how many warps may reside; timing shows which block size is faster here.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <vector>

__global__ void resource_kernel(float* output, int n) {
    extern __shared__ float shared[];
    const int i = blockIdx.x * blockDim.x + threadIdx.x;

    // Every thread contributes one value before the block-wide barrier.
    shared[threadIdx.x] = static_cast<float>(threadIdx.x);
    __syncthreads();

    if (i < n) {
        // value is a private automatic scalar and is normally held in a register.
        const float value = shared[threadIdx.x] * 2.0f + 1.0f;
        output[i] = value;
    }
}

int main() {
    int device = 0;
    check_cuda(cudaGetDevice(&device), "get active device");
    cudaDeviceProp p{};
    check_cuda(cudaGetDeviceProperties(&p, device), "query device properties");

    cudaFuncAttributes attributes{};
    check_cuda(cudaFuncGetAttributes(&attributes, resource_kernel), "query resource_kernel attributes");

    const int block_sizes[] = {32, 64, 128, 256, 512, 1024};
    constexpr int elements = 4 * 1024 * 1024;
    constexpr int repetitions = 50;
    constexpr int measurement_rounds = 5;
    const std::size_t output_bytes = static_cast<std::size_t>(elements) * sizeof(float);
    std::vector<float> output_h(elements);
    float* output_d = nullptr;
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&output_d), output_bytes), "allocate benchmark output");

    std::cout << "Device: " << p.name << '\n' << "Maximum threads/SM: " << p.maxThreadsPerMultiProcessor << '\n' << "Warp size: " << p.warpSize << '\n'
              << "Kernel registers/thread: " << attributes.numRegs << '\n' << "Elements: " << elements << ", timing: median of " << measurement_rounds << " rounds, " << repetitions
              << " launches per round\n\n" << std::left << std::setw(8) << "Block" << std::setw(13) << "Shared B" << std::setw(12) << "Blocks/SM" << std::setw(12) << "Warps/SM"
              << std::setw(13) << "Occupancy %" << std::setw(13) << "Kernel ms" << std::setw(15) << "G elements/s" << "Max error\n";

    bool all_correct = true;
    int fastest_block = 0;
    float fastest_ms = std::numeric_limits<float>::max();
    double fastest_occupancy = 0.0;

    for (const int block_size : block_sizes) {
        if (block_size > p.maxThreadsPerBlock) {
            continue;
        }
        const std::size_t dynamic_shared = block_size * sizeof(float);
        int active_blocks = 0;
        check_cuda(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&active_blocks, resource_kernel, block_size, dynamic_shared), "calculate active blocks per SM");

        const int warps_per_block = (block_size + p.warpSize - 1) / p.warpSize;
        const int active_warps = active_blocks * warps_per_block;
        const int max_warps = p.maxThreadsPerMultiProcessor / p.warpSize;
        const double occupancy = static_cast<double>(active_warps) / max_warps;
        const int grid_size = (elements + block_size - 1) / block_size;

        resource_kernel<<<grid_size, block_size, dynamic_shared>>>(output_d, elements);
        check_cuda(cudaGetLastError(), "launch resource_kernel warm-up");
        check_cuda(cudaDeviceSynchronize(), "execute resource_kernel warm-up");

        std::vector<float> samples;
        samples.reserve(measurement_rounds);
        for (int round = 0; round < measurement_rounds; ++round) {
            const float total_ms = time_cuda_ms([&] {
                for (int repetition = 0; repetition < repetitions; ++repetition) {
                    resource_kernel<<<grid_size, block_size, dynamic_shared>>>(output_d, elements);
                }
                check_cuda(cudaGetLastError(), "launch timed resource_kernel instances");
            });
            samples.push_back(total_ms / repetitions);
        }

        const float kernel_ms = median_cuda_ms(samples);
        const double billion_elements_per_second = static_cast<double>(elements) / (kernel_ms * 1.0e6);
        check_cuda(cudaMemcpy(output_h.data(), output_d, output_bytes, cudaMemcpyDeviceToHost), "copy benchmark output");

        float maximum_error = 0.0f;
        for (int i = 0; i < elements; ++i) {
            const float expected = static_cast<float>(i % block_size) * 2.0f + 1.0f;
            maximum_error = std::max(maximum_error, std::fabs(output_h[i] - expected));
        }
        all_correct = all_correct && maximum_error == 0.0f;

        if (kernel_ms < fastest_ms) {
            fastest_ms = kernel_ms;
            fastest_block = block_size;
            fastest_occupancy = occupancy;
        }

        std::cout << std::left << std::setw(8) << block_size << std::setw(13) << dynamic_shared << std::setw(12) << active_blocks << std::setw(12) << active_warps << std::fixed
                  << std::setprecision(1) << std::setw(13) << 100.0 * occupancy << std::setprecision(4) << std::setw(13) << kernel_ms << std::setw(15) << billion_elements_per_second
                  << maximum_error << '\n';
    }

    check_cuda(cudaFree(output_d), "free benchmark output");

    /*
     * The occupancy API models resource residency; it does not time the kernel.
     * A lower-occupancy kernel can be faster if it gains more useful work per
     * thread, better locality, or fewer instructions. Measure after reasoning.
     */
    std::cout << "\nFastest measured block size: " << fastest_block << " threads (" << std::fixed << std::setprecision(1) << 100.0 * fastest_occupancy << "% theoretical occupancy, "
              << std::setprecision(4) << fastest_ms << " ms)\n"
              << "Measured time, not occupancy alone, decides which configuration is faster.\n";
    return all_correct ? EXIT_SUCCESS : EXIT_FAILURE;
}
