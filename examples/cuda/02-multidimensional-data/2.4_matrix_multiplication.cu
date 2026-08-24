/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 2.4_matrix_multiplication
 *   make condor_run build/2.4_matrix_multiplication
 *   make condor_submit build/2.4_matrix_multiplication
 *
 * Section 2.4: Naive matrix multiplication with one thread per output
 *
 * Matrix shapes:
 *
 *     A is M x K
 *     B is K x N
 *     C is M x N
 *
 * C(row,col) is the dot product of row row from A and column col from B:
 *
 *     C[row,col] = sum over k of A[row,k] * B[k,col]
 *
 * A 2D grid assigns one thread to each C element. The thread is parallel with
 * other output threads, but its K-term dot product remains a sequential loop.
 *
 * The CPU loop supplies an independent correctness reference. This file is a
 * mapping baseline, not a performance experiment; Section 4.4 compares this
 * global-memory algorithm with shared-memory tiling on the same GPU.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <vector>


__global__ void matmul_kernel(const float* a, const float* b, float* c, int m, int k_size, int n) {
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    const int row = blockIdx.y * blockDim.y + threadIdx.y;

    if (row < m && col < n) {
        float sum = 0.0f; // A private per-thread scalar, normally a register.
        for (int k = 0; k < k_size; ++k) {
            /*
             * Row-major addresses:
             * A[row,k] -> row*k_size + k
             * B[k,col] -> k*n + col
             *
             * Moving along an A row changes addresses by one. Moving down a B
             * column changes addresses by n.
             */
            sum += a[row * k_size + k] * b[k * n + col];
        }
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
    /*
     * The dimensions are not divisible by the 16x16 block shape. They also
     * exercise all row, column, and inner-dimension boundary conditions.
     */
    const int m = 513;
    const int k_size = 511;
    const int n = 515;

    std::vector<float> a_h(m * k_size);
    std::vector<float> b_h(k_size * n);
    std::vector<float> expected_h(m * n);
    std::vector<float> c_h(m * n);
    for (std::size_t i = 0; i < a_h.size(); ++i) {
        a_h[i] = static_cast<float>(i % 7) - 3.0f;
    }
    for (std::size_t i = 0; i < b_h.size(); ++i) {
        b_h[i] = static_cast<float>(i % 5) * 0.5f;
    }
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

    const dim3 block(16, 16);
    const dim3 grid((n + block.x - 1) / block.x, (m + block.y - 1) / block.y);
    matmul_kernel<<<grid, block>>>(a_d, b_d, c_d, m, k_size, n);
    check_cuda(cudaGetLastError(), "launch matmul_kernel");
    check_cuda(cudaDeviceSynchronize(), "execute matmul_kernel");
    check_cuda(cudaMemcpy(c_h.data(), c_d, c_bytes, cudaMemcpyDeviceToHost), "copy C D2H");
    check_cuda(cudaFree(a_d), "cudaFree A");
    check_cuda(cudaFree(b_d), "cudaFree B");
    check_cuda(cudaFree(c_d), "cudaFree C");

    float max_abs_error = 0.0f;
    for (std::size_t i = 0; i < c_h.size(); ++i) {
        max_abs_error = std::max(max_abs_error, std::fabs(c_h[i] - expected_h[i]));
    }
    std::cout << "A: " << m << 'x' << k_size << ", B: " << k_size << 'x' << n << ", C: " << m << 'x' << n << '\n'
              << "Outputs checked against CPU reference: " << c_h.size() << '\n' << "Maximum absolute error: " << max_abs_error << '\n';
    return max_abs_error <= 1.0e-4f ? EXIT_SUCCESS : EXIT_FAILURE;
}

/*
 * This is a correct baseline, not a fast GEMM. Threads repeatedly load
 * overlapping A and B values from global memory. The memory-locality module
 * tiles these inputs into shared memory to reuse them within a block.
 */
