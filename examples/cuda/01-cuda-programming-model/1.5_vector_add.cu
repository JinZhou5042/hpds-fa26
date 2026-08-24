/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 1.5_vector_add
 *   make condor_run build/1.5_vector_add
 *   make condor_submit build/1.5_vector_add
 *
 * Section 1.5: Complete CUDA vector addition
 *
 * This combines the earlier CPU loop, grid indexing, and memory transfers. The
 * data path is:
 *
 *   host A, B --H2D--> device A, B --kernel--> device C --D2H--> host C
 *
 * H2D means Host to Device. D2H means Device to Host.
 *
 * A basic CUDA program follows five steps:
 *
 * 1. cudaMalloc: allocate device global memory;
 * 2. H2D cudaMemcpy: send inputs to the GPU;
 * 3. <<<grid, block>>>: launch the kernel;
 * 4. D2H cudaMemcpy: retrieve the output from the GPU;
 * 5. cudaFree: release device memory.
 *
 * Four elements keep every transfer and result easy to inspect. This is a
 * complete execution-path example, not a performance experiment. The topic's
 * overall program uses a large vector for a meaningful timing comparison.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <vector>


__global__ void vector_add_kernel(const float* a_d, const float* b_d, float* c_d, std::size_t n) {
    /*
     * Ordinary host code cannot dereference these device addresses, but a
     * kernel executing on the GPU can.
     *
     * Convert blockIdx.x to size_t before multiplication so a very large grid
     * does not compute the intermediate product in a narrower integer type.
     * Every thread owns a private copy of the local variable i.
     */
    const std::size_t i = static_cast<std::size_t>(blockIdx.x) * blockDim.x + threadIdx.x;

    // A rounded-up grid has extra threads; only valid indices may touch arrays.
    if (i < n) {
        /*
         * Each valid thread performs two global-memory reads, one floating-point
         * addition, and one global-memory write. Threads write distinct C[i]
         * elements, so there is no data race and no need for atomics or
         * __syncthreads().
         */
        c_d[i] = a_d[i] + b_d[i];
    }
}

void vector_add_cpu(const float* a, const float* b, float* c, std::size_t n) {
    for (std::size_t i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

int main() {
    /*
     * std::vector stores data in memory directly accessible to the CPU. N stays
     * at four so the result remains easy to verify by inspection.
     */
    const std::vector<float> a_h{1.0f, 2.0f, 3.0f, 4.0f};
    const std::vector<float> b_h{10.0f, 20.0f, 30.0f, 40.0f};
    std::vector<float> c_h(a_h.size());
    std::vector<float> c_cpu(a_h.size());

    // n counts elements; CUDA memory APIs require a count in bytes.
    const std::size_t n = a_h.size();
    const std::size_t bytes = n * sizeof(float);

    vector_add_cpu(a_h.data(), b_h.data(), c_cpu.data(), n);

    /*
     * These three pointer variables live on the host, but after cudaMalloc they
     * contain addresses in device memory. Initialize them to nullptr rather
     * than leaving indeterminate pointer values.
     */
    float* a_d = nullptr;
    float* b_d = nullptr;
    float* c_d = nullptr;

    /*
     * 1. Allocate three arrays in GPU global memory.
     *
     * cudaMalloc takes void** because it modifies the pointer itself, storing a
     * newly allocated device address in a_d, b_d, or c_d. reinterpret_cast only
     * converts float** into the void** type required by the API; it does not
     * copy any data.
     *
     * cudaMalloc allocates storage but does not initialize it. The contents of
     * c_d are undefined until the kernel writes them.
     */
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&a_d), bytes), "cudaMalloc A");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&b_d), bytes), "cudaMalloc B");
    check_cuda(cudaMalloc(reinterpret_cast<void**>(&c_d), bytes), "cudaMalloc C");

    /*
     * 2. Copy both inputs explicitly.
     *
     * cudaMemcpy(dst, src, bytes, direction) always places the destination
     * first and the source second. cudaMemcpyHostToDevice states which memory
     * spaces those addresses belong to.
     *
     * There is no reason to copy c_h into c_d because the kernel overwrites
     * every valid output element.
     */
    check_cuda(cudaMemcpy(a_d, a_h.data(), bytes, cudaMemcpyHostToDevice), "copy A host to device");
    check_cuda(cudaMemcpy(b_d, b_h.data(), bytes, cudaMemcpyHostToDevice), "copy B host to device");

    /*
     * 3. Launch enough GPU threads.
     *
     * A block size of 256 is a common starting point because it is a multiple
     * of the usual warp size of 32 and provides several warps for an SM to
     * schedule. It is not universally optimal for every kernel and GPU.
     *
     * Here N=4, so grid_size=1 still launches 256 threads. Only indices 0..3 do
     * work; if(i<n) suppresses the other 252. This is wasteful for such a tiny
     * demonstration but semantically correct.
     */
    const int block_size = 256;
    const std::size_t grid_size = (n + block_size - 1) / block_size;
    vector_add_kernel<<<static_cast<unsigned int>(grid_size), block_size>>>(a_d, b_d, c_d, n);

    /*
     * A kernel launch normally returns asynchronously. cudaDeviceSynchronize()
     * waits for completion so later code can safely use the output and so
     * execution errors that occurred after launch are reported to the host.
     */
    check_cuda(cudaGetLastError(), "launch vector_add_kernel");
    check_cuda(cudaDeviceSynchronize(), "execute vector_add_kernel");

    /*
     * 4. Copy the GPU result into the host vector.
     *
     * The CPU cannot directly read an ordinary c_d allocated by cudaMalloc; a
     * D2H copy is required. This cudaMemcpy call is synchronous with respect to
     * the host, so c_h is ready for CPU access when the call returns.
     */
    check_cuda(cudaMemcpy(c_h.data(), c_d, bytes, cudaMemcpyDeviceToHost), "copy C device to host");

    /*
     * 5. Release GPU memory.
     *
     * std::vector automatically releases host memory, but every successful
     * cudaMalloc in this example requires a matching cudaFree. Omitting it
     * produces a device-memory leak.
     */
    check_cuda(cudaFree(a_d), "cudaFree A");
    check_cuda(cudaFree(b_d), "cudaFree B");
    check_cuda(cudaFree(c_d), "cudaFree C");

    float max_abs_error = 0.0f;
    for (std::size_t i = 0; i < n; ++i) {
        std::cout << "c[" << i << "] = " << c_h[i] << '\n';
        max_abs_error = std::max(max_abs_error, std::fabs(c_h[i] - c_cpu[i]));
    }
    std::cout << "Elements checked against CPU reference: " << n << '\n' << "Maximum absolute error: " << max_abs_error << '\n';
    return max_abs_error <= 1.0e-5f ? EXIT_SUCCESS : EXIT_FAILURE;
}
