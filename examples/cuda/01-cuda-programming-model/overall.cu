/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make overall
 *   make condor_run build/overall
 *   make condor_submit build/overall
 *
 * Overall program: Complete heterogeneous vector addition
 *
 * Usage:
 *
 *     ./overall [N] [BLOCK_SIZE]
 *     ./overall 100003 257
 *
 * Follow main from top to bottom:
 *
 * host preparation -> device query -> allocation -> H2D -> grid launch ->
 * synchronization -> D2H -> validation -> deallocation.
 *
 * This topic summary uses a large vector for a compute-only CPU/GPU comparison.
 * Allocation and transfers are intentionally outside the measured regions.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>


/*
 * __global__ declares a kernel. a_d and b_d are read-only device pointers;
 * c_d is writable. The grid replaces the CPU for-loop: thread i performs the
 * work that loop iteration i performs in vector_add_cpu.
 */
__global__ void vector_add_kernel(const float* a_d, const float* b_d, float* c_d, std::size_t n) {
    const std::size_t i = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (i < n) {
        c_d[i] = a_d[i] + b_d[i];
    }
}

void vector_add_cpu(const float* a, const float* b, float* c, std::size_t n) {
    for (std::size_t i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

std::size_t parse_positive_size(const char* text, const char* name) {
    std::size_t consumed = 0;
    unsigned long long value = 0;
    try {
        value = std::stoull(text, &consumed);
    } catch (const std::exception&) {
        throw std::invalid_argument(std::string(name) + " must be an integer");
    }
    if (consumed != std::string(text).size() || value == 0 || value > std::numeric_limits<std::size_t>::max()) {
        throw std::invalid_argument(std::string(name) + " must be positive");
    }
    return static_cast<std::size_t>(value);
}

int main(int argc, char** argv) {
    try {
        if (argc > 3) {
            throw std::invalid_argument("Usage: overall [N] [BLOCK_SIZE]");
        }

        const std::size_t n = argc >= 2 ? parse_positive_size(argv[1], "N") : 1'000'003;
        const std::size_t parsed_block = argc >= 3 ? parse_positive_size(argv[2], "BLOCK_SIZE") : 256;
        if (parsed_block > static_cast<std::size_t>(std::numeric_limits<int>::max())) {
            throw std::invalid_argument("BLOCK_SIZE is too large for int");
        }
        const int block_size = static_cast<int>(parsed_block);

        /*
         * Multiplication used for an allocation size must be checked for integer
         * overflow before it is performed. Otherwise a huge N could wrap bytes
         * to a small value and make later array accesses unsafe.
         */
        if (n > std::numeric_limits<std::size_t>::max() / sizeof(float)) {
            throw std::overflow_error("N overflows the byte count");
        }
        const std::size_t bytes = n * sizeof(float);

        int device = 0;
        CUDA_CHECK(cudaGetDevice(&device));
        cudaDeviceProp properties{};
        CUDA_CHECK(cudaGetDeviceProperties(&properties, device));
        if (block_size > properties.maxThreadsPerBlock) {
            throw std::invalid_argument("BLOCK_SIZE exceeds this device's maxThreadsPerBlock");
        }

        /*
         * Ceiling division creates enough whole blocks to cover n. CUDA launch
         * dimensions have implementation limits, so validate before casting the
         * size_t grid count to the unsigned type accepted by this launch.
         */
        const std::size_t grid_size = 1 + (n - 1) / block_size;
        if (grid_size > static_cast<std::size_t>(properties.maxGridSize[0])) {
            throw std::invalid_argument("N requires too many x-dimension blocks");
        }

        std::cout << "Device: " << properties.name << '\n' << "Compute capability: " << properties.major << '.' << properties.minor << '\n' << "N: " << n << '\n'
                  << "Block size: " << block_size << '\n' << "Grid size: " << grid_size << '\n' << "Threads launched: " << grid_size * block_size << '\n'
                  << "Inactive tail threads: " << grid_size * block_size - n << "\n\n";

        // Host vectors own ordinary CPU memory and initialize deterministic data.
        std::vector<float> a_h(n);
        std::vector<float> b_h(n);
        std::vector<float> c_reference(n);
        std::vector<float> c_gpu(n);
        for (std::size_t i = 0; i < n; ++i) {
            a_h[i] = static_cast<float>(i % 1009) * 0.001f;
            b_h[i] = static_cast<float>(i % 1013) * 0.002f - 0.5f;
        }
        constexpr int cpu_repetitions = 20;
        constexpr int gpu_repetitions = 100;
        constexpr int measurement_rounds = 5;
        vector_add_cpu(a_h.data(), b_h.data(), c_reference.data(), n);
        const auto cpu_start = std::chrono::steady_clock::now();
        for (int repetition = 0; repetition < cpu_repetitions; ++repetition) {
            vector_add_cpu(a_h.data(), b_h.data(), c_reference.data(), n);
        }
        const auto cpu_stop = std::chrono::steady_clock::now();
        const double cpu_ms = std::chrono::duration<double, std::milli>(cpu_stop - cpu_start).count() / cpu_repetitions;

        // These host variables will hold addresses in device global memory.
        float* a_d = nullptr;
        float* b_d = nullptr;
        float* c_d = nullptr;
        CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&a_d), bytes));
        CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&b_d), bytes));
        CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&c_d), bytes));

        CUDA_CHECK(cudaMemcpy(a_d, a_h.data(), bytes, cudaMemcpyHostToDevice));
        CUDA_CHECK(cudaMemcpy(b_d, b_h.data(), bytes, cudaMemcpyHostToDevice));
        vector_add_kernel<<<static_cast<unsigned int>(grid_size), block_size>>>(a_d, b_d, c_d, n);
        CUDA_CHECK(cudaGetLastError());
        CUDA_CHECK(cudaDeviceSynchronize());

        std::vector<float> gpu_samples;
        gpu_samples.reserve(measurement_rounds);
        for (int round = 0; round < measurement_rounds; ++round) {
            const float total_ms = time_cuda_ms([&] {
                for (int repetition = 0; repetition < gpu_repetitions; ++repetition) {
                    vector_add_kernel<<<static_cast<unsigned int>(grid_size), block_size>>>(a_d, b_d, c_d, n);
                }
                CUDA_CHECK(cudaGetLastError());
            });
            gpu_samples.push_back(total_ms / gpu_repetitions);
        }
        const float gpu_ms = median_cuda_ms(gpu_samples);

        CUDA_CHECK(cudaMemcpy(c_gpu.data(), c_d, bytes, cudaMemcpyDeviceToHost));

        CUDA_CHECK(cudaFree(a_d));
        CUDA_CHECK(cudaFree(b_d));
        CUDA_CHECK(cudaFree(c_d));

        float max_abs_error = 0.0f;
        std::size_t first_mismatch = n;
        for (std::size_t i = 0; i < n; ++i) {
            const float error = std::fabs(c_gpu[i] - c_reference[i]);
            max_abs_error = std::max(max_abs_error, error);
            if (error > 1.0e-5f && first_mismatch == n) {
                first_mismatch = i;
            }
        }

        if (first_mismatch != n) {
            std::cerr << "First mismatch at " << first_mismatch << ": expected " << c_reference[first_mismatch] << ", received " << c_gpu[first_mismatch] << '\n';
        }
        std::cout << "Compute-only timing: CPU average of " << cpu_repetitions << " runs; GPU median of " << measurement_rounds << " rounds, "
                  << gpu_repetitions << " launches per round.\n"
                  << "CPU computation time: " << cpu_ms << " ms\n" << "GPU kernel time (memory copies excluded): " << gpu_ms << " ms\n"
                  << "GPU speedup over CPU (CPU time / GPU time): " << cpu_ms / gpu_ms << "x\n" << "Maximum absolute error: " << max_abs_error << '\n';
        return first_mismatch == n ? EXIT_SUCCESS : EXIT_FAILURE;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
