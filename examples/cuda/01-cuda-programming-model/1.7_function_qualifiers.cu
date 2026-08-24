/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 1.7_function_qualifiers
 *   make condor_run build/1.7_function_qualifiers
 *   make condor_submit build/1.7_function_qualifiers
 *
 * Section 1.7: Function qualifiers, compilation, and error visibility
 *
 * CUDA source mixes host and device code in one .cu file. nvcc separates the
 * two worlds and coordinates a host C++ compiler with NVIDIA's device compiler.
 * The host portion becomes ordinary CPU code. The device portion can become
 * PTX, NVIDIA's virtual GPU instruction set, which is converted into machine
 * code for the target GPU before execution.
 *
 * CUDA has three function qualifiers:
 *
 * __host__   : runs on the CPU and is called from host code;
 * __device__ : runs on the GPU and is called from device code;
 * __global__ : a kernel that runs on the GPU and is launched with <<<...>>>.
 *
 * An unqualified function is a host function by default. A function marked both
 * __host__ and __device__ is compiled twice, producing one version for each
 * processor. Its body must use operations supported in both compilation paths.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>


// nvcc creates both a CPU and a GPU implementation of this pure arithmetic.
__host__ __device__ float affine(float x, float scale, float bias) { return scale * x + bias; }

// Only device code can call this helper. Calling it from main would not compile.
__device__ float clamp_zero_to_one(float x) {
    if (x < 0.0f) {
        return 0.0f;
    }
    if (x > 1.0f) {
        return 1.0f;
    }
    return x;
}

// Host code launches this function; many GPU threads execute its body.
__global__ void transform_kernel(const float* input, float* output, int n, float scale, float bias) {
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        output[i] = clamp_zero_to_one(affine(input[i], scale, bias));
    }
}

void transform_cpu(const float* input, float* output, int n, float scale, float bias) {
    for (int i = 0; i < n; ++i) {
        // Host code cannot call the __device__ helper, so it reproduces the same clamp rule independently.
        const float transformed = affine(input[i], scale, bias);
        output[i] = std::max(0.0f, std::min(1.0f, transformed));
    }
}

int main() {
    constexpr int n = 5;
    const float input_h[n] = {-1.0f, 0.0f, 0.25f, 0.75f, 2.0f};
    float output_h[n] = {};
    float expected_h[n] = {};
    constexpr std::size_t bytes = n * sizeof(float);

    // This call selects the host version of the dual-compiled affine function.
    std::cout << "Host affine(0.25, 2, -0.25) = " << affine(0.25f, 2.0f, -0.25f) << '\n';
    transform_cpu(input_h, expected_h, n, 2.0f, -0.25f);

    float* input_d = nullptr;
    float* output_d = nullptr;
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&input_d), bytes), "cudaMalloc input");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&output_d), bytes), "cudaMalloc output");
    check_cuda(cudaMemcpy(input_d, input_h, bytes, cudaMemcpyHostToDevice), "copy input H2D");
    transform_kernel<<<1, 32>>>(input_d, output_d, n, 2.0f, -0.25f);

    /*
     * cudaGetLastError checks launch setup: invalid block dimensions, invalid
     * arguments, or another immediate launch failure. The GPU may still be
     * executing successfully or unsuccessfully after this call returns.
     */
    check_cuda(cudaGetLastError(), "launch transform_kernel");

    /*
     * cudaDeviceSynchronize waits for execution and reports asynchronous faults
     * such as illegal device-memory accesses. Checking both calls distinguishes
     * launch errors from errors discovered while the GPU runs the kernel.
     */
    check_cuda(cudaDeviceSynchronize(), "execute transform_kernel");
    check_cuda(cudaMemcpy(output_h, output_d, bytes, cudaMemcpyDeviceToHost), "copy output D2H");

    check_cuda(cudaFree(input_d), "cudaFree input");
    check_cuda(cudaFree(output_d), "cudaFree output");

    float max_abs_error = 0.0f;
    for (int i = 0; i < n; ++i) {
        std::cout << "output[" << i << "] = " << output_h[i] << ", expected " << expected_h[i] << '\n';
        max_abs_error = std::max(max_abs_error, std::fabs(output_h[i] - expected_h[i]));
    }
    std::cout << "Host and device implementations checked: " << n << " values\n"
              << "Maximum absolute error: " << max_abs_error << '\n';

    return max_abs_error <= 1.0e-6f ? EXIT_SUCCESS : EXIT_FAILURE;
}
