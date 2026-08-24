/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 4.6_dynamic_shared_occupancy
 *   make condor_run build/4.6_dynamic_shared_occupancy
 *   make condor_submit build/4.6_dynamic_shared_occupancy
 *
 * Section 4.6: Dynamic shared memory and occupancy tradeoffs
 *
 * Dynamic shared memory is declared without a compile-time size:
 *
 *     extern __shared__ float tile[];
 *
 * The third launch parameter selects the bytes reserved by every block:
 *
 *     kernel<<<grid, block, shared_bytes>>>(...);
 *
 * This controlled experiment keeps the kernel and useful work unchanged while
 * increasing only the per-block shared-memory reservation. Extra bytes are
 * intentionally unused: they create resource pressure without changing the
 * answer or operation count. The table places modeled occupancy beside measured
 * time. Occupancy is latency-hiding capacity, not a performance score, so the
 * fastest row need not be the row with the highest occupancy.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>

__global__ void dynamic_shared_kernel(const float* input, float* output, int n) {
    extern __shared__ float tile[];
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    tile[threadIdx.x] = i < n ? input[i] : 0.0f;
    __syncthreads();
    if (i < n) {
        output[i] = tile[threadIdx.x] * 2.0f;
    }
}

struct Configuration {
    std::size_t shared_bytes;
    int blocks_per_sm;
    int active_warps;
    double occupancy;
    std::vector<float> samples;
};

int main() {
    int device = 0;
    CUDA_CHECK(cudaGetDevice(&device));
    cudaDeviceProp properties{};
    CUDA_CHECK(cudaGetDeviceProperties(&properties, device));

    constexpr int block_size = 256;
    constexpr int elements = 16 * 1024 * 1024;
    constexpr int repetitions = 20;
    constexpr int measurement_rounds = 5;
    constexpr std::size_t required_tile_bytes = block_size * sizeof(float);
    const std::size_t requested_reservations[] = {required_tile_bytes, 16 * 1024, 32 * 1024, 48 * 1024};
    const int maximum_warps = properties.maxThreadsPerMultiProcessor / properties.warpSize;
    const int warps_per_block = block_size / properties.warpSize;

    std::vector<Configuration> configurations;
    for (const std::size_t shared_bytes : requested_reservations) {
        if (shared_bytes > properties.sharedMemPerBlock) {
            continue;
        }
        int blocks_per_sm = 0;
        CUDA_CHECK(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&blocks_per_sm, dynamic_shared_kernel, block_size, shared_bytes));
        const int active_warps = blocks_per_sm * warps_per_block;
        configurations.push_back({shared_bytes, blocks_per_sm, active_warps, static_cast<double>(active_warps) / maximum_warps, {}});
        configurations.back().samples.reserve(measurement_rounds);
    }

    if (configurations.empty()) {
        std::cerr << "No requested shared-memory reservation is supported by this GPU.\n";
        return EXIT_FAILURE;
    }

    const std::size_t bytes = static_cast<std::size_t>(elements) * sizeof(float);
    std::vector<float> input_h(elements, 3.0f);
    std::vector<float> output_h(elements);
    float* input_d = nullptr;
    float* output_d = nullptr;
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&input_d), bytes));
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&output_d), bytes));
    CUDA_CHECK(cudaMemcpy(input_d, input_h.data(), bytes, cudaMemcpyHostToDevice));
    const int grid_size = (elements + block_size - 1) / block_size;

    // Warm every launch configuration before collecting samples.
    for (const Configuration& configuration : configurations) {
        dynamic_shared_kernel<<<grid_size, block_size, configuration.shared_bytes>>>(input_d, output_d, elements);
    }
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());

    const auto measure = [&](Configuration& configuration) {
        const float total_ms = time_cuda_ms([&] {
            for (int repetition = 0; repetition < repetitions; ++repetition) {
                dynamic_shared_kernel<<<grid_size, block_size, configuration.shared_bytes>>>(input_d, output_d, elements);
            }
            CUDA_CHECK(cudaGetLastError());
        });
        configuration.samples.push_back(total_ms / repetitions);
    };

    // Reverse alternate rounds to reduce systematic clock and thermal bias.
    for (int round = 0; round < measurement_rounds; ++round) {
        if ((round & 1) == 0) {
            for (Configuration& configuration : configurations) {
                measure(configuration);
            }
        } else {
            for (auto configuration = configurations.rbegin(); configuration != configurations.rend(); ++configuration) {
                measure(*configuration);
            }
        }
    }

    CUDA_CHECK(cudaMemcpy(output_h.data(), output_d, bytes, cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaFree(input_d));
    CUDA_CHECK(cudaFree(output_d));

    float maximum_error = 0.0f;
    for (const float value : output_h) {
        maximum_error = std::max(maximum_error, std::fabs(value - 6.0f));
    }

    std::cout << "Device: " << properties.name << '\n'
              << "Shared memory/block limit: " << properties.sharedMemPerBlock << " bytes\n"
              << "Elements: " << elements << ", block size: " << block_size << '\n'
              << "Each row performs identical work; only reserved shared memory changes.\n"
              << "Timing: median of " << measurement_rounds << " rounds, " << repetitions << " launches per round; memory copies excluded.\n\n"
              << std::left << std::setw(18) << "Reserved bytes" << std::setw(12) << "Blocks/SM" << std::setw(12) << "Warps/SM" << std::setw(14) << "Occupancy %"
              << std::setw(14) << "Time (ms)" << "Bandwidth GB/s\n";

    float fastest_ms = 0.0f;
    std::size_t fastest_shared_bytes = 0;
    for (const Configuration& configuration : configurations) {
        const float kernel_ms = median_cuda_ms(configuration.samples);
        const double bandwidth_gbs = 2.0 * bytes / (kernel_ms * 1.0e6);
        if (fastest_shared_bytes == 0 || kernel_ms < fastest_ms) {
            fastest_ms = kernel_ms;
            fastest_shared_bytes = configuration.shared_bytes;
        }
        std::cout << std::left << std::setw(18) << configuration.shared_bytes << std::setw(12) << configuration.blocks_per_sm << std::setw(12)
                  << configuration.active_warps << std::fixed << std::setprecision(1) << std::setw(14) << 100.0 * configuration.occupancy << std::setprecision(4)
                  << std::setw(14) << kernel_ms << bandwidth_gbs << '\n';
    }

    std::cout << "\nFastest measured reservation: " << fastest_shared_bytes << " bytes/block\n"
              << "Occupancy estimates resident warp capacity; measured time decides performance.\n"
              << "Maximum absolute error: " << maximum_error << '\n';
    return maximum_error == 0.0f ? EXIT_SUCCESS : EXIT_FAILURE;
}
