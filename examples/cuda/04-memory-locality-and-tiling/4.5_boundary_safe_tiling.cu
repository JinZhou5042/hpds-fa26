/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 4.5_boundary_safe_tiling
 *   make condor_run build/4.5_boundary_safe_tiling
 *   make condor_submit build/4.5_boundary_safe_tiling
 *
 * Section 4.5: Boundary-safe tiled multiplication for rectangular matrices
 *
 * General shapes are A(MxK) * B(KxN) = C(MxN). M, K, and N need not be tile
 * multiples. Check the three boundaries separately:
 *
 * - A load is valid when row<M and a_col<K;
 * - B load is valid when b_row<K and col<N;
 * - C store is valid when row<M and col<N.
 *
 * Invalid input loads store zero into shared memory. Zero is the neutral value
 * for addition in the dot product and safely pads incomplete tiles.
 *
 * Threads with invalid C coordinates must still participate in tile loads and
 * both barriers. Returning early could deprive valid peers of inputs or violate
 * the block-wide barrier contract.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <vector>

constexpr int kTile = 16;


__global__ void tiled_matmul_rectangular(const float* a, const float* b, float* c, int m, int k_size, int n) {
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

        a_tile[ty][tx] = (row < m && a_col < k_size) ? a[row * k_size + a_col] : 0.0f;
        b_tile[ty][tx] = (b_row < k_size && col < n) ? b[b_row * n + col] : 0.0f;
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

void matmul_cpu(const std::vector<float>& a, const std::vector<float>& b, std::vector<float>& c, int m, int k_size, int n) {
    for (int row = 0; row < m; ++row) {
        for (int col = 0; col < n; ++col) {
            float sum = 0.0f;
            for (int k = 0; k < k_size; ++k) {
                sum += a[row * k_size + k] * b[k * n + col];
            }
            c[row * n + col] = sum;
        }
    }
}

int main() {
    constexpr int m = 37;
    constexpr int k_size = 29;
    constexpr int n = 41;
    std::vector<float> a_h(m * k_size);
    std::vector<float> b_h(k_size * n);
    std::vector<float> expected_h(m * n);
    std::vector<float> c_h(m * n);
    for (std::size_t i = 0; i < a_h.size(); ++i)
        a_h[i] = (i % 9) * 0.125f;
    for (std::size_t i = 0; i < b_h.size(); ++i)
        b_h[i] = (i % 7) * 0.25f - 0.5f;
    matmul_cpu(a_h, b_h, expected_h, m, k_size, n);

    float* a_d = nullptr;
    float* b_d = nullptr;
    float* c_d = nullptr;
    const std::size_t a_bytes = a_h.size() * sizeof(float);
    const std::size_t b_bytes = b_h.size() * sizeof(float);
    const std::size_t c_bytes = c_h.size() * sizeof(float);
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&a_d), a_bytes), "cudaMalloc A");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&b_d), b_bytes), "cudaMalloc B");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&c_d), c_bytes), "cudaMalloc C");
    check_cuda(cudaMemcpy(a_d, a_h.data(), a_bytes, cudaMemcpyHostToDevice), "copy A H2D");
    check_cuda(cudaMemcpy(b_d, b_h.data(), b_bytes, cudaMemcpyHostToDevice), "copy B H2D");
    const dim3 block(kTile, kTile);
    const dim3 grid((n + kTile - 1) / kTile, (m + kTile - 1) / kTile);
    tiled_matmul_rectangular<<<grid, block>>>(a_d, b_d, c_d, m, k_size, n);
    check_cuda(cudaGetLastError(), "launch tiled_matmul_rectangular");
    check_cuda(cudaDeviceSynchronize(), "execute tiled_matmul_rectangular");
    check_cuda(cudaMemcpy(c_h.data(), c_d, c_bytes, cudaMemcpyDeviceToHost), "copy C D2H");
    check_cuda(cudaFree(a_d), "cudaFree A");
    check_cuda(cudaFree(b_d), "cudaFree B");
    check_cuda(cudaFree(c_d), "cudaFree C");

    float max_error = 0.0f;
    for (std::size_t i = 0; i < c_h.size(); ++i) {
        max_error = std::max(max_error, std::fabs(c_h[i] - expected_h[i]));
    }
    const std::size_t output_threads = static_cast<std::size_t>(grid.x) * grid.y * block.x * block.y;
    std::cout << "A: " << m << 'x' << k_size << ", B: " << k_size << 'x' << n << '\n'
              << "Tile: " << kTile << 'x' << kTile << ", phases: " << (k_size + kTile - 1) / kTile << '\n'
              << "Grid: " << grid.x << 'x' << grid.y << " blocks\n"
              << "Valid outputs: " << static_cast<std::size_t>(m) * n << '\n'
              << "Threads outside C boundary: " << output_threads - static_cast<std::size_t>(m) * n << '\n'
              << "All valid outputs checked against CPU reference.\n"
              << "Maximum absolute error: " << max_error << '\n';
    return max_error <= 1.0e-4f ? EXIT_SUCCESS : EXIT_FAILURE;
}
