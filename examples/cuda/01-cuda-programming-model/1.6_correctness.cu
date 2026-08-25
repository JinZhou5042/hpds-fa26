/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 1.6_correctness
 *   ./1.6_correctness
 *
 * Section 1.6: Validate GPU correctness with a CPU reference
 *
 * A successful kernel launch does not prove that its output is correct. This
 * version compares every GPU result with an independent CPU calculation.
 *
 * N=1003 is not divisible by the 128-thread block size, so the run also checks
 * ceiling division and the boundary guard in the final block. Floating-point
 * values are compared with a tolerance and summarized by maximum absolute
 * error.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <vector>


void vector_add_cpu(const float* a, const float* b, float* c, std::size_t n) {
    // A simple CPU implementation provides an independently computed answer.
    for (std::size_t i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

__global__ void vector_add_kernel(const float* a_d, const float* b_d, float* c_d, std::size_t n) {
    // Flatten each thread's block-local identity into one global array index.
    const std::size_t i = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;

    // Without this check, the final 21 threads would access beyond the arrays.
    if (i < n) {
        c_d[i] = a_d[i] + b_d[i];
    }
}

int main() {
    /*
     * ceil(1003/128) = 8, so the launch contains 8*128 = 1024 threads.
     *
     * - the first seven blocks cover indices 0..895;
     * - the first 107 threads of the final block cover 896..1002;
     * - the last 21 threads produce 1003..1023 and fail the boundary check.
     *
     * A 128-thread block contains four 32-thread warps. Unlike the four-thread
     * small launch in Section 1.3, it is a plausible practical block size, but this
     * does not establish that 128 is optimal.
     */
    const std::size_t n = 1003;
    const int block_size = 128;
    const std::size_t grid_size = (n + block_size - 1) / block_size;
    const std::size_t bytes = n * sizeof(float);

    /*
     * Keep two distinct outputs:
     *
     * c_cpu: the CPU reference;
     * c_gpu: the tested result copied back from the device.
     *
     * Printing only a few values could easily miss an error in the middle or at
     * the end of the array.
     */
    std::vector<float> a_h(n);
    std::vector<float> b_h(n);
    std::vector<float> c_cpu(n);
    std::vector<float> c_gpu(n);

    /*
     * Use deterministic rather than random inputs so every run reproduces the
     * same problem. i%17 varies B periodically without allowing values to grow
     * excessively large.
     */
    for (std::size_t i = 0; i < n; ++i) {
        a_h[i] = static_cast<float>(i) * 0.25f;
        b_h[i] = static_cast<float>(i % 17) - 3.0f;
    }
    // Produce the trusted host reference before beginning GPU work.
    vector_add_cpu(a_h.data(), b_h.data(), c_cpu.data(), n);

    // This is Section 1.5's allocate -> H2D -> kernel -> D2H -> free sequence.
    float* a_d = nullptr;
    float* b_d = nullptr;
    float* c_d = nullptr;
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&a_d), bytes), "cudaMalloc A");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&b_d), bytes), "cudaMalloc B");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&c_d), bytes), "cudaMalloc C");
    check_cuda(cudaMemcpy(a_d, a_h.data(), bytes, cudaMemcpyHostToDevice), "copy A host to device");
    check_cuda(cudaMemcpy(b_d, b_h.data(), bytes, cudaMemcpyHostToDevice), "copy B host to device");
    vector_add_kernel<<<static_cast<unsigned int>(grid_size), block_size>>>(a_d, b_d, c_d, n);
    check_cuda(cudaGetLastError(), "launch vector_add_kernel");
    check_cuda(cudaDeviceSynchronize(), "execute vector_add_kernel");
    check_cuda(cudaMemcpy(c_gpu.data(), c_d, bytes, cudaMemcpyDeviceToHost), "copy C device to host");

    check_cuda(cudaFree(a_d), "cudaFree A");
    check_cuda(cudaFree(b_d), "cudaFree B");
    check_cuda(cudaFree(c_d), "cudaFree C");

    /*
     * Compute |GPU[i]-CPU[i]| for every element and retain the maximum. A value
     * of zero means the two implementations matched exactly for this input. It
     * is not a mathematical proof for every possible input, but it is much more
     * meaningful than spot-checking a few printed values.
     *
     * Why not use c_gpu[i] == c_cpu[i]? Reordered floating-point operations,
     * fused multiply-add instructions, compiler options, and different hardware
     * can introduce small rounding differences. This kernel normally matches
     * exactly because each output performs the same single addition, but using a
     * tolerance establishes a habit that generalizes to more complex kernels.
     */
    float max_abs_error = 0.0f;
    for (std::size_t i = 0; i < n; ++i) {
        max_abs_error = std::max(max_abs_error, std::fabs(c_gpu[i] - c_cpu[i]));
    }

    std::cout << "N: " << n << '\n' << "Block size: " << block_size << '\n' << "Grid size: " << grid_size << '\n' << "Threads launched: " << grid_size * block_size << '\n'
              << "Unused threads in final block: " << grid_size * block_size - n << '\n'
              << "Elements checked against CPU reference: " << n << '\n' << "Maximum absolute error: " << max_abs_error << '\n';

    /*
     * 1e-5 is a strict absolute tolerance for this input range. General numeric
     * software often combines absolute and relative tolerances:
     *
     *     |x-y| <= atol + rtol*|reference|
     *
     * A fixed absolute tolerance may be inappropriate for values that are very
     * large or extremely close to zero.
     */
    return max_abs_error <= 1.0e-5f ? EXIT_SUCCESS : EXIT_FAILURE;
}
