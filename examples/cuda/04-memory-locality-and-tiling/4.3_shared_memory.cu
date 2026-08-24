/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 4.3_shared_memory
 *   make condor_run build/4.3_shared_memory
 *   make condor_submit build/4.3_shared_memory
 *
 * Section 4.3: Cooperative loading and reuse in shared memory
 *
 * This experiment compares two GPU kernels that do identical arithmetic.
 * Every block owns one input tile, and every thread sums every value in that
 * tile:
 *
 * - without reuse, every thread reads the complete tile from global memory;
 * - with reuse, the block cooperatively loads the tile once into shared memory.
 *
 * The source-level global-load count falls by a factor of TILE_WIDTH. Hardware
 * caches and warp broadcasts can reduce actual memory transactions, while the
 * shared-memory version pays for a barrier. Measured speedup must therefore be
 * observed rather than inferred from the load count alone.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>

constexpr int kTile = 256;

__global__ void global_reuse_kernel(const float* input, float* output) {
    const int tile_start = blockIdx.x * blockDim.x;
    float sum = 0.0f;

    // Every thread independently issues TILE_WIDTH global-memory loads.
    for (int k = 0; k < kTile; ++k) {
        sum += input[tile_start + k];
    }
    output[tile_start + threadIdx.x] = sum;
}

__global__ void shared_reuse_kernel(const float* input, float* output) {
    __shared__ float tile[kTile];
    const int tile_start = blockIdx.x * blockDim.x;

    // Cooperative load: TILE_WIDTH threads perform TILE_WIDTH global loads.
    tile[threadIdx.x] = input[tile_start + threadIdx.x];

    // Read-after-write barrier: the complete tile must be visible before reuse.
    __syncthreads();

    float sum = 0.0f;
    for (int k = 0; k < kTile; ++k) {
        sum += tile[k];
    }
    output[tile_start + threadIdx.x] = sum;
}

float maximum_difference(const std::vector<float>& a, const std::vector<float>& b) {
    float result = 0.0f;
    for (std::size_t i = 0; i < a.size(); ++i) {
        result = std::max(result, std::fabs(a[i] - b[i]));
    }
    return result;
}

int main() {
    constexpr int blocks = 4096;
    constexpr int repetitions = 10;
    constexpr int measurement_rounds = 5;
    constexpr std::size_t elements = static_cast<std::size_t>(blocks) * kTile;
    constexpr std::size_t bytes = elements * sizeof(float);

    std::vector<float> input_h(elements);
    std::vector<float> global_h(elements);
    std::vector<float> shared_h(elements);
    for (std::size_t i = 0; i < elements; ++i) {
        input_h[i] = static_cast<float>(i % 17) * 0.0625f;
    }

    float* input_d = nullptr;
    float* global_d = nullptr;
    float* shared_d = nullptr;
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&input_d), bytes));
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&global_d), bytes));
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&shared_d), bytes));
    CUDA_CHECK(cudaMemcpy(input_d, input_h.data(), bytes, cudaMemcpyHostToDevice));

    global_reuse_kernel<<<blocks, kTile>>>(input_d, global_d);
    shared_reuse_kernel<<<blocks, kTile>>>(input_d, shared_d);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());

    std::vector<float> global_samples;
    std::vector<float> shared_samples;
    global_samples.reserve(measurement_rounds);
    shared_samples.reserve(measurement_rounds);

    const auto measure_global = [&] {
        const float total_ms = time_cuda_ms([&] {
            for (int repetition = 0; repetition < repetitions; ++repetition) {
                global_reuse_kernel<<<blocks, kTile>>>(input_d, global_d);
            }
            CUDA_CHECK(cudaGetLastError());
        });
        global_samples.push_back(total_ms / repetitions);
    };
    const auto measure_shared = [&] {
        const float total_ms = time_cuda_ms([&] {
            for (int repetition = 0; repetition < repetitions; ++repetition) {
                shared_reuse_kernel<<<blocks, kTile>>>(input_d, shared_d);
            }
            CUDA_CHECK(cudaGetLastError());
        });
        shared_samples.push_back(total_ms / repetitions);
    };

    // Alternate order to reduce systematic clock and thermal bias.
    for (int round = 0; round < measurement_rounds; ++round) {
        if ((round & 1) == 0) {
            measure_global();
            measure_shared();
        } else {
            measure_shared();
            measure_global();
        }
    }

    CUDA_CHECK(cudaMemcpy(global_h.data(), global_d, bytes, cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(shared_h.data(), shared_d, bytes, cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaFree(input_d));
    CUDA_CHECK(cudaFree(global_d));
    CUDA_CHECK(cudaFree(shared_d));

    const float global_ms = median_cuda_ms(global_samples);
    const float shared_ms = median_cuda_ms(shared_samples);
    const float max_difference = maximum_difference(global_h, shared_h);
    const double additions = static_cast<double>(elements) * kTile;
    const auto giga_additions_per_second = [=](float milliseconds) { return additions / (milliseconds * 1.0e6); };

    std::cout << "Blocks: " << blocks << ", threads/block: " << kTile << ", output elements: " << elements << '\n'
              << "Modeled global loads/block without reuse: " << kTile * kTile << '\n'
              << "Modeled global loads/block with reuse: " << kTile << '\n'
              << "Source-level global-load reduction: " << kTile << "x\n"
              << "Timing: median of " << measurement_rounds << " rounds, " << repetitions << " launches per round\n\n"
              << std::left << std::setw(22) << "GPU kernel" << std::right << std::setw(14) << "Time (ms)" << std::setw(18) << "Useful Gadd/s" << '\n'
              << std::left << std::setw(22) << "Global loads" << std::right << std::setw(14) << global_ms << std::setw(18)
              << giga_additions_per_second(global_ms) << '\n'
              << std::left << std::setw(22) << "Shared-memory reuse" << std::right << std::setw(14) << shared_ms << std::setw(18)
              << giga_additions_per_second(shared_ms) << "\n\n"
              << "Speedup from shared reuse (global / shared): " << global_ms / shared_ms << "x\n"
              << "Maximum absolute difference: " << max_difference << '\n';
    return max_difference == 0.0f ? EXIT_SUCCESS : EXIT_FAILURE;
}
