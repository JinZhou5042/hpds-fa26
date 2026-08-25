/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 3.1_device_properties
 *   ./3.1_device_properties
 *
 * Section 3.1: Query the hardware that will execute this program
 *
 * CUDA code is portable across devices, but device resources are not identical.
 * Query capabilities instead of hard-coding assumptions about block limits,
 * grid limits, SM count, warp size, registers, or shared memory.
 *
 * Compute capability major.minor identifies an NVIDIA architecture feature set.
 * It is not a direct speed rating. Performance also depends on SM count, clock,
 * memory system, instruction mix, and the application's bottleneck.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include <cstdlib>
#include <iomanip>
#include <iostream>


int main() {
    int device_count = 0;
    check_cuda(cudaGetDeviceCount(&device_count), "cudaGetDeviceCount");
    if (device_count == 0) {
        std::cerr << "No CUDA devices are visible\n";
        return EXIT_FAILURE;
    }

    std::cout << "Visible CUDA devices: " << device_count << "\n\n";
    for (int device = 0; device < device_count; ++device) {
        cudaDeviceProp p{};
        check_cuda(cudaGetDeviceProperties(&p, device), "cudaGetDeviceProperties");

        const int max_warps_per_sm = p.maxThreadsPerMultiProcessor / p.warpSize;
        std::cout << "Device " << device << ": " << p.name << '\n' << "  Compute capability: " << p.major << '.' << p.minor << '\n' << "  Streaming multiprocessors: " << p.multiProcessorCount << '\n'
                  << "  Warp size: " << p.warpSize << " threads\n" << "  Maximum resident threads/SM: " << p.maxThreadsPerMultiProcessor << '\n'
                  << "  Maximum resident warps/SM: " << max_warps_per_sm << '\n' << "  Maximum threads/block: " << p.maxThreadsPerBlock << '\n'
                  << "  Maximum block dimensions: (" << p.maxThreadsDim[0] << ',' << p.maxThreadsDim[1] << ',' << p.maxThreadsDim[2] << ")\n"
                  << "  Maximum grid dimensions: (" << p.maxGridSize[0] << ',' << p.maxGridSize[1] << ',' << p.maxGridSize[2] << ")\n" << "  Registers/block limit: " << p.regsPerBlock << '\n'
                  << "  Shared memory/block: " << p.sharedMemPerBlock / 1024.0 << " KiB\n" << "  Shared memory/SM: " << p.sharedMemPerMultiprocessor / 1024.0 << " KiB\n"
                  << "  Global memory: " << std::fixed << std::setprecision(2) << p.totalGlobalMem / (1024.0 * 1024.0 * 1024.0) << " GiB\n\n";
    }

    /*
     * These are capacity limits, not promises that a kernel reaches them all at
     * once. Threads, blocks, registers, and shared memory are simultaneous
     * constraints. The tightest resource determines residency and occupancy.
     */
}
