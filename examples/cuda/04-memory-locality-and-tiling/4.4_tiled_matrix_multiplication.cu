/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 4.4_tiled_matrix_multiplication
 *   ./4.4_tiled_matrix_multiplication
 *
 * Section 4.4: Tiled matrix multiplication with static shared memory
 *
 * The experiment compares two GPU kernels that perform the same arithmetic:
 * one reads every operand directly from global memory, while the other reuses
 * operands from shared-memory tiles. CPU performance is not part of this
 * comparison.
 *
 * Both kernels assume square matrices whose width is divisible by TILE_WIDTH.
 * Section 4.5 removes those simplifying assumptions.
 *
 * Each block computes one TILE_WIDTH x TILE_WIDTH tile of C. Each phase:
 *
 * 1. every thread loads one A element and one B element into shared memory;
 * 2. a barrier waits for the complete tiles;
 * 3. every thread reuses the tiles for TILE_WIDTH multiply-add iterations;
 * 4. a barrier waits before the shared arrays are overwritten next phase.
 *
 * This is strip-mining: split a long K loop into tile-sized phases.
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

__global__ void naive_matmul_kernel(const float* a, const float* b, float* c, int width) {
    const int row = blockIdx.y * blockDim.y + threadIdx.y;
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    float sum = 0.0f;

    // Every use reads A and B from global memory; there is no block-level reuse.
    for (int k = 0; k < width; ++k) {
        sum += a[row * width + k] * b[k * width + col];
    }
    c[row * width + col] = sum;
}

__global__ void tiled_matmul_kernel(const float* a, const float* b, float* c, int width) {
    __shared__ float a_tile[kTile][kTile];
    __shared__ float b_tile[kTile][kTile];

    const int tx = threadIdx.x;
    const int ty = threadIdx.y;
    const int row = blockIdx.y * kTile + ty;
    const int col = blockIdx.x * kTile + tx;
    float sum = 0.0f;

    for (int phase = 0; phase < width / kTile; ++phase) {
        /*
         * The block's 256 threads cooperatively load 256 A values and 256 B
         * values. Neighboring tx values load neighboring row-major addresses,
         * giving a favorable coalesced global access pattern.
         */
        a_tile[ty][tx] = a[row * width + phase * kTile + tx];
        b_tile[ty][tx] = b[(phase * kTile + ty) * width + col];

        // Read-after-write: every tile element must be ready before reuse.
        __syncthreads();

        for (int k = 0; k < kTile; ++k) {
            sum += a_tile[ty][k] * b_tile[k][tx];
        }

        // Write-after-read: no thread may overwrite a tile still being consumed.
        __syncthreads();
    }
    c[row * width + col] = sum;
}

int main() {
    // A large matrix makes arithmetic and memory traffic dominate launch cost.
    constexpr int width = 3200;
    constexpr int repetitions = 5;
    constexpr int measurement_rounds = 5;
    const std::size_t elements = static_cast<std::size_t>(width) * width;
    const std::size_t bytes = elements * sizeof(float);
    std::vector<float> a_h(elements, 0.5f);
    std::vector<float> b_h(elements, 0.25f);
    std::vector<float> naive_h(elements);
    std::vector<float> tiled_h(elements);

    float* a_d = nullptr;
    float* b_d = nullptr;
    float* naive_d = nullptr;
    float* tiled_d = nullptr;
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&a_d), bytes), "cudaMalloc A");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&b_d), bytes), "cudaMalloc B");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&naive_d), bytes), "cudaMalloc naive C");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&tiled_d), bytes), "cudaMalloc tiled C");
    check_cuda(cudaMemcpy(a_d, a_h.data(), bytes, cudaMemcpyHostToDevice), "copy A H2D");
    check_cuda(cudaMemcpy(b_d, b_h.data(), bytes, cudaMemcpyHostToDevice), "copy B H2D");

    const dim3 block(kTile, kTile);
    const dim3 grid(width / kTile, width / kTile);

    naive_matmul_kernel<<<grid, block>>>(a_d, b_d, naive_d, width);
    tiled_matmul_kernel<<<grid, block>>>(a_d, b_d, tiled_d, width);
    check_cuda(cudaGetLastError(), "launch warm-up naive_matmul_kernel");
    check_cuda(cudaDeviceSynchronize(), "execute warm-up matrix kernels");

    std::vector<float> naive_samples;
    std::vector<float> tiled_samples;
    naive_samples.reserve(measurement_rounds);
    tiled_samples.reserve(measurement_rounds);
    const auto measure_naive = [&] {
        const float total_ms = time_cuda_ms([&] {
            for (int run = 0; run < repetitions; ++run) {
                naive_matmul_kernel<<<grid, block>>>(a_d, b_d, naive_d, width);
            }
            check_cuda(cudaGetLastError(), "launch timed naive_matmul_kernel");
        });
        naive_samples.push_back(total_ms / repetitions);
    };
    const auto measure_tiled = [&] {
        const float total_ms = time_cuda_ms([&] {
            for (int run = 0; run < repetitions; ++run) {
                tiled_matmul_kernel<<<grid, block>>>(a_d, b_d, tiled_d, width);
            }
            check_cuda(cudaGetLastError(), "launch timed tiled_matmul_kernel");
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

    check_cuda(cudaMemcpy(naive_h.data(), naive_d, bytes, cudaMemcpyDeviceToHost), "copy naive C D2H");
    check_cuda(cudaMemcpy(tiled_h.data(), tiled_d, bytes, cudaMemcpyDeviceToHost), "copy tiled C D2H");

    check_cuda(cudaFree(a_d), "cudaFree A");
    check_cuda(cudaFree(b_d), "cudaFree B");
    check_cuda(cudaFree(naive_d), "cudaFree naive C");
    check_cuda(cudaFree(tiled_d), "cudaFree tiled C");

    const float expected = width * 0.5f * 0.25f;
    float naive_error = 0.0f;
    float tiled_error = 0.0f;
    for (std::size_t i = 0; i < elements; ++i) {
        naive_error = std::max(naive_error, std::fabs(naive_h[i] - expected));
        tiled_error = std::max(tiled_error, std::fabs(tiled_h[i] - expected));
    }

    const float naive_ms = median_cuda_ms(naive_samples);
    const float tiled_ms = median_cuda_ms(tiled_samples);
    const double operations = 2.0 * width * width * width;
    const double naive_gflops = operations / (naive_ms * 1.0e6);
    const double tiled_gflops = operations / (tiled_ms * 1.0e6);

    std::cout << "Matrix: " << width << " x " << width << '\n'
              << "Tile width: " << kTile << ", phases: " << width / kTile << '\n'
              << "Shared memory/block: " << 2 * kTile * kTile * sizeof(float) << " bytes\n"
              << "Approximate global-load reduction from tiling: " << kTile << "x\n"
              << "Timing: median of " << measurement_rounds << " rounds, " << repetitions << " launches per round; memory copies excluded.\n\n"
              << std::left << std::setw(22) << "GPU kernel" << std::right << std::setw(14) << "Time (ms)"
              << std::setw(14) << "GFLOP/s" << std::setw(14) << "Max error" << '\n'
              << std::left << std::setw(22) << "Without tiling" << std::right << std::setw(14) << naive_ms
              << std::setw(14) << naive_gflops << std::setw(14) << naive_error << '\n'
              << std::left << std::setw(22) << "With tiling" << std::right << std::setw(14) << tiled_ms
              << std::setw(14) << tiled_gflops << std::setw(14) << tiled_error << "\n\n"
              << "Speedup from tiling (without / with): " << naive_ms / tiled_ms << "x\n";
    return naive_error <= 1.0e-4f && tiled_error <= 1.0e-4f ? EXIT_SUCCESS : EXIT_FAILURE;
}

/*
 * In the naive kernel, overlapping global inputs are independently fetched by
 * many threads. Here each tile element is loaded once per block phase and reused
 * by TILE_WIDTH threads. The simplified reduction in global loads is therefore
 * approximately TILE_WIDTH, increasing arithmetic intensity.
 */
