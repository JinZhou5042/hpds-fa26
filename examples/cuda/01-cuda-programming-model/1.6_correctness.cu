/*
 * From this topic directory (see ../README.md for details).
 *
 * HTCondor (Notre Dame CRC): build on the front end, run on a GPU worker
 *   module load cuda/12.1
 *   make 1.6_correctness
 *   ./1.6_correctness
 *
 * Slurm (Purdue Anvil): build on the login node, run with sbatch
 *   module load modtree/gpu cuda/12.8.0
 *   make 1.6_correctness
 *   sbatch ../common/anvil_gpu.slurm ./1.6_correctness
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


void vector_add_cpu(const float* a, const float* b, float* c, int n) {
    // A simple CPU implementation provides an independently computed answer.
    for (int i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

__global__ void vector_add_kernel(const float* a_d, const float* b_d, float* c_d, int n) {
    // Flatten each thread's block-local identity into one global array index.
    const int i = blockIdx.x * blockDim.x + threadIdx.x;

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
    const int n = 1003;
    const int block_size = 128;
    const int grid_size = (n + block_size - 1) / block_size;
    const int bytes = n * sizeof(float);

    /*
     * Keep two distinct outputs:
     *
     * c_cpu: the CPU reference;
     * c_gpu: the tested result copied back from the device.
     *
     * Printing only a few values could easily miss an error in the middle or at
     * the end of the array.
     */
     float a_h[n];
     float b_h[n];
     float c_cpu[n];
     float c_gpu[n];

    /*
     * Use deterministic rather than random inputs so every run reproduces the
     * same problem. i%17 varies B periodically without allowing values to grow
     * excessively large.
     */
    for (int i = 0; i < n; ++i) {
        a_h[i] = (float)(i) * 0.25f;
        b_h[i] = (float)(i % 17) - 3.0f;
    }
    // Produce the trusted host reference before beginning GPU work.
    vector_add_cpu(a_h, b_h, c_cpu, n);

    // This is Section 1.5's allocate -> H2D -> kernel -> D2H -> free sequence.
    float* a_d = nullptr;
    float* b_d = nullptr;
    float* c_d = nullptr;

    check_cuda(cudaMalloc((void**)(&a_d), bytes), "cudaMalloc A");
    check_cuda(cudaMalloc((void**)(&b_d), bytes), "cudaMalloc B");
    check_cuda(cudaMalloc((void**)(&c_d), bytes), "cudaMalloc C");

    check_cuda(cudaMemcpy(a_d, a_h, bytes, cudaMemcpyHostToDevice), "copy A host to device");
    check_cuda(cudaMemcpy(b_d, b_h, bytes, cudaMemcpyHostToDevice), "copy B host to device");

    vector_add_kernel<<<grid_size, block_size>>>(a_d, b_d, c_d, n);

    check_cuda(cudaGetLastError(), "launch vector_add_kernel");
    check_cuda(cudaDeviceSynchronize(), "execute vector_add_kernel");

    check_cuda(cudaMemcpy(c_gpu, c_d, bytes, cudaMemcpyDeviceToHost), "copy C device to host");

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
    for (int i = 0; i < n; ++i) {
        max_abs_error = std::max(max_abs_error, std::fabs(c_gpu[i] - c_cpu[i]));
    }

    printf("N: %d\n",n);
    printf("Block size: %d\n",block_size);
    printf("Grid size: %d\n",grid_size);
    printf("Threads launched: %d\n",grid_size*block_size);
    printf("Unused threads in final block: %d\n",grid_size*block_size -n);
    printf("Elements checked against CPU reference: %d\n",n);
    printf("Maximum absolute error: %f\n",max_abs_error);

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
