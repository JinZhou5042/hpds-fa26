/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 4.2_arithmetic_intensity
 *   ./4.2_arithmetic_intensity
 *
 * Section 4.2: Arithmetic intensity and a roofline-style bandwidth ceiling
 *
 * Arithmetic intensity = useful operations / bytes transferred from the memory
 * level being analyzed. It helps identify whether performance is likely limited
 * by memory bandwidth or compute throughput.
 *
 * Naive matrix multiplication inner iteration:
 *
 * - load A: 4 bytes;
 * - load B: 4 bytes;
 * - multiply and add: 2 FLOPs;
 * - intensity: 2/8 = 0.25 FLOP/byte.
 *
 * A tiled algorithm reuses each global load approximately TILE_WIDTH times, so
 * its simplified intensity grows to roughly 0.25*TILE_WIDTH FLOP/byte.
 */

#include <cuda_runtime.h>

#include <cstdlib>
#include <iomanip>
#include <iostream>

int main() {
    int device = 0;
    cudaGetDevice(&device);
    cudaDeviceProp p{};
    const cudaError_t error = cudaGetDeviceProperties(&p, device);
    if (error != cudaSuccess) {
        std::cerr << cudaGetErrorString(error) << '\n';
        return EXIT_FAILURE;
    }

    /*
     * memoryClockRate is in kHz and memoryBusWidth is in bits. DDR transfers on
     * both clock edges, so a simple theoretical bandwidth estimate is:
     *
     * 2 * clock_hz * (bus_bits/8) bytes/second.
     *
     * This is a hardware peak, not an achievable application measurement.
     */
    const double peak_bandwidth_gbs = 2.0 * p.memoryClockRate * 1000.0 * (p.memoryBusWidth / 8.0) / 1.0e9;

    std::cout << "Device: " << p.name << '\n' << "Estimated peak memory bandwidth: " << std::fixed << std::setprecision(1) << peak_bandwidth_gbs << " GB/s\n\n"
              << std::left << std::setw(12) << "Tile width" << std::setw(18) << "Approx FLOP/B" << "Bandwidth roof (GFLOP/s)\n";

    const int tile_widths[] = {1, 8, 16, 32};
    for (const int tile : tile_widths) {
        const double intensity = 0.25 * tile;
        const double bandwidth_roof_gflops = peak_bandwidth_gbs * intensity;
        std::cout << std::left << std::setw(12) << tile << std::setw(18) << std::setprecision(2) << intensity << std::setprecision(1) << bandwidth_roof_gflops << '\n';
    }

    std::cout << "\nA roof is an upper bound. Poor coalescing, latency, instruction "
                 "overhead, or insufficient parallelism can place real results "
                 "well below it.\n";
}
