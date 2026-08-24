/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make overall
 *   make condor_run build/overall
 *   make condor_submit build/overall
 *
 * Overall program: Naive versus tiled matrix multiplication
 *
 * Two kernels multiply the same rectangular matrices:
 *
 * - naive: every thread repeatedly loads its A row and B column from global;
 * - tiled: each block cooperatively stages reusable A/B tiles in shared memory.
 *
 * The output includes kernel time, modeled occupancy, and numerical error.
 * Tiling reduces global-memory traffic, but the speedup depends on the GPU.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <vector>

constexpr int kTile = 16;


__global__ void naive_matmul(const float* a, const float* b, float* c, int m, int k_size, int n) {
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    const int row = blockIdx.y * blockDim.y + threadIdx.y;
    if (row < m && col < n) {
        float sum = 0.0f;
        for (int k = 0; k < k_size; ++k) {
            sum += a[row * k_size + k] * b[k * n + col];
        }
        c[row * n + col] = sum;
    }
}

__global__ void tiled_matmul(const float* a, const float* b, float* c, int m, int k_size, int n) {
    __shared__ float a_tile[kTile][kTile];
    __shared__ float b_tile[kTile][kTile];
    const int tx = threadIdx.x;
    const int ty = threadIdx.y;
    const int row = blockIdx.y * kTile + ty;
    const int col = blockIdx.x * kTile + tx;
    const int phases = (k_size + kTile - 1) / kTile;
    float sum = 0.0f;

    for (int phase = 0; phase < phases; ++phase) {
        const int a_col = phase * kTile + tx;
        const int b_row = phase * kTile + ty;
        a_tile[ty][tx] = row < m && a_col < k_size ? a[row * k_size + a_col] : 0.0f;
        b_tile[ty][tx] = b_row < k_size && col < n ? b[b_row * n + col] : 0.0f;
        __syncthreads();
        for (int k = 0; k < kTile; ++k) {
            sum += a_tile[ty][k] * b_tile[k][tx];
        }
        __syncthreads();
    }
    if (row < m && col < n) {
        c[row * n + col] = sum;
    }
}


float maximum_error(const std::vector<float>& actual, float expected) {
    float result = 0.0f;
    for (const float value : actual) {
        result = std::max(result, std::fabs(value - expected));
    }
    return result;
}

int main() {
    // Odd rectangular dimensions exercise all three boundary conditions.
    constexpr int m = 1601;
    constexpr int k_size = 1603;
    constexpr int n = 1607;
    constexpr int repetitions = 5;
    constexpr int measurement_rounds = 5;

    const std::size_t a_elements = static_cast<std::size_t>(m) * k_size;
    const std::size_t b_elements = static_cast<std::size_t>(k_size) * n;
    const std::size_t c_elements = static_cast<std::size_t>(m) * n;
    std::vector<float> a_h(a_elements, 0.5f);
    std::vector<float> b_h(b_elements, 0.25f);
    std::vector<float> naive_h(c_elements);
    std::vector<float> tiled_h(c_elements);

    float* a_d = nullptr;
    float* b_d = nullptr;
    float* naive_d = nullptr;
    float* tiled_d = nullptr;
    const std::size_t a_bytes = a_h.size() * sizeof(float);
    const std::size_t b_bytes = b_h.size() * sizeof(float);
    const std::size_t c_bytes = c_elements * sizeof(float);
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&a_d), a_bytes));
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&b_d), b_bytes));
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&naive_d), c_bytes));
    CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&tiled_d), c_bytes));
    CUDA_CHECK(cudaMemcpy(a_d, a_h.data(), a_bytes, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(b_d, b_h.data(), b_bytes, cudaMemcpyHostToDevice));

    const dim3 block(kTile, kTile);
    const dim3 grid((n + kTile - 1) / kTile, (m + kTile - 1) / kTile);

    naive_matmul<<<grid, block>>>(a_d, b_d, naive_d, m, k_size, n);
    tiled_matmul<<<grid, block>>>(a_d, b_d, tiled_d, m, k_size, n);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());

    std::vector<float> naive_samples;
    std::vector<float> tiled_samples;
    naive_samples.reserve(measurement_rounds);
    tiled_samples.reserve(measurement_rounds);
    const auto measure_naive = [&] {
        const float total_ms = time_cuda_ms([&] {
            for (int repetition = 0; repetition < repetitions; ++repetition) {
                naive_matmul<<<grid, block>>>(a_d, b_d, naive_d, m, k_size, n);
            }
            CUDA_CHECK(cudaGetLastError());
        });
        naive_samples.push_back(total_ms / repetitions);
    };
    const auto measure_tiled = [&] {
        const float total_ms = time_cuda_ms([&] {
            for (int repetition = 0; repetition < repetitions; ++repetition) {
                tiled_matmul<<<grid, block>>>(a_d, b_d, tiled_d, m, k_size, n);
            }
            CUDA_CHECK(cudaGetLastError());
        });
        tiled_samples.push_back(total_ms / repetitions);
    };

    for (int round = 0; round < measurement_rounds; ++round) {
        if ((round & 1) == 0) {
            measure_naive();
            measure_tiled();
        } else {
            measure_tiled();
            measure_naive();
        }
    }

    CUDA_CHECK(cudaMemcpy(naive_h.data(), naive_d, c_bytes, cudaMemcpyDeviceToHost));
    CUDA_CHECK(cudaMemcpy(tiled_h.data(), tiled_d, c_bytes, cudaMemcpyDeviceToHost));

    int naive_blocks_per_sm = 0;
    int tiled_blocks_per_sm = 0;
    CUDA_CHECK(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&naive_blocks_per_sm, naive_matmul, kTile * kTile, 0));
    CUDA_CHECK(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&tiled_blocks_per_sm, tiled_matmul, kTile * kTile, 0));

    CUDA_CHECK(cudaFree(a_d));
    CUDA_CHECK(cudaFree(b_d));
    CUDA_CHECK(cudaFree(naive_d));
    CUDA_CHECK(cudaFree(tiled_d));

    const float expected = k_size * 0.5f * 0.25f;
    const float naive_error = maximum_error(naive_h, expected);
    const float tiled_error = maximum_error(tiled_h, expected);
    const float naive_ms = median_cuda_ms(naive_samples);
    const float tiled_ms = median_cuda_ms(tiled_samples);
    const double operations = 2.0 * m * k_size * n;
    const double naive_gflops = operations / (naive_ms * 1.0e6);
    const double tiled_gflops = operations / (tiled_ms * 1.0e6);
    const bool correct = naive_error <= 1.0e-3f && tiled_error <= 1.0e-3f;

    std::cout << "A: " << m << 'x' << k_size << ", B: " << k_size << 'x' << n << '\n'
              << "Tile: " << kTile << 'x' << kTile << ", static shared/block: " << 2 * kTile * kTile * sizeof(float) << " bytes\n"
              << "Approximate global-load reduction from tiling: " << kTile << "x\n"
              << "Timing: median of " << measurement_rounds << " rounds, " << repetitions << " launches per round; memory copies excluded.\n\n"
              << std::left << std::setw(12) << "GPU kernel" << std::right << std::setw(14) << "Time (ms)" << std::setw(14) << "GFLOP/s" << std::setw(14)
              << "Blocks/SM" << std::setw(14) << "Max error" << '\n'
              << std::left << std::setw(12) << "Naive" << std::right << std::setw(14) << naive_ms << std::setw(14) << naive_gflops << std::setw(14)
              << naive_blocks_per_sm << std::setw(14) << naive_error << '\n'
              << std::left << std::setw(12) << "Tiled" << std::right << std::setw(14) << tiled_ms << std::setw(14) << tiled_gflops << std::setw(14)
              << tiled_blocks_per_sm << std::setw(14) << tiled_error << '\n'
              << "Tiled speedup over naive GPU (naive / tiled): " << naive_ms / tiled_ms << "x\n";
    return correct ? EXIT_SUCCESS : EXIT_FAILURE;
}
