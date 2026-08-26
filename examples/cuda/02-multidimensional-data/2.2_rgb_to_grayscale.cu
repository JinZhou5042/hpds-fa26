/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 2.2_rgb_to_grayscale
 *   ./2.2_rgb_to_grayscale bird.png bird_grayscale.png
 *
 * Section 2.2: Convert an RGB PNG to grayscale
 *
 * A two-dimensional CUDA thread coordinate selects one pixel and its three RGB
 * bytes.
 *
 * The host uses libpng through png_io.h to decode INPUT.png into this flat,
 * row-major byte layout:
 *
 *     R0 G0 B0 | R1 G1 B1 | R2 G2 B2 | ...
 *
 * The kernel never sees PNG compression. It receives decoded bytes, writes one
 * grayscale byte per pixel, and leaves PNG encoding to the host.
 *
 * Each thread follows these mappings:
 *
 *     col = blockIdx.x * blockDim.x + threadIdx.x
 *     row = blockIdx.y * blockDim.y + threadIdx.y
 *     pixel = row * width + col
 *     RGB byte offset = 3 * pixel
 *
 * Command-line arguments:
 *
 * 1. input PNG path;
 * 2. output grayscale PNG path.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include "png_io.h"

#include <algorithm>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <vector>


__global__ void rgb_to_grayscale_kernel(const unsigned char* rgb, unsigned char* gray, int width, int height) {
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    const int row = blockIdx.y * blockDim.y + threadIdx.y;

    // Ceiling division may launch threads past the image, so only valid coordinates may access memory.
    if (row < height && col < width) {
        const int pixel = row * width + col;
        const int rgb_offset = 3 * pixel;
        const unsigned int r = rgb[rgb_offset];
        const unsigned int g = rgb[rgb_offset + 1];
        const unsigned int b = rgb[rgb_offset + 2];

        /*
         * Human vision is more sensitive to green than red and more sensitive
         * to red than blue, so grayscale is a weighted sum rather than a plain
         * average. These integer weights approximate 0.21R + 0.72G + 0.07B.
         * They sum to 100, keep the result in [0, 255], and make CPU/GPU
         * comparison exactly reproducible for byte-valued input.
         */
        gray[pixel] = static_cast<unsigned char>((21u * r + 72u * g + 7u * b) / 100u);
    }
}

void grayscale_cpu(const std::vector<unsigned char>& rgb, std::vector<unsigned char>& gray) {
    for (std::size_t pixel = 0; pixel < gray.size(); ++pixel) {
        const std::size_t rgb_offset = 3 * pixel;
        const unsigned int r = rgb[rgb_offset];
        const unsigned int g = rgb[rgb_offset + 1];
        const unsigned int b = rgb[rgb_offset + 2];
        gray[pixel] = static_cast<unsigned char>((21u * r + 72u * g + 7u * b) / 100u);
    }
}

int maximum_byte_difference(const std::vector<unsigned char>& actual, const std::vector<unsigned char>& expected) {
    int maximum = 0;
    for (std::size_t i = 0; i < actual.size(); ++i) {
        maximum = std::max(maximum, std::abs(static_cast<int>(actual[i]) - static_cast<int>(expected[i])));
    }
    return maximum;
}

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " INPUT.png OUTPUT.png\n";
        return EXIT_FAILURE;
    }

    try {
        int width = 0;
        int height = 0;
        const std::vector<unsigned char> rgb_h = png_io::read_rgb_png(argv[1], width, height);
        const std::size_t pixels = static_cast<std::size_t>(width) * height;
        const std::size_t rgb_bytes = 3 * pixels;
        const std::size_t gray_bytes = pixels;
        std::vector<unsigned char> gray_gpu(pixels);
        std::vector<unsigned char> gray_reference(pixels);

        grayscale_cpu(rgb_h, gray_reference);

        /*
         * The _h and _d suffixes are common CUDA naming conventions:
         * _h means host memory and _d means device memory. They are not part
         * of the language, but they make each pointer's address space visible.
         */
        unsigned char* rgb_d = nullptr;
        unsigned char* gray_d = nullptr;
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&rgb_d), rgb_bytes), "cudaMalloc RGB");
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&gray_d), gray_bytes), "cudaMalloc grayscale");
        check_cuda(cudaMemcpy(rgb_d, rgb_h.data(), rgb_bytes, cudaMemcpyHostToDevice), "copy RGB H2D");

        // A 16x16 block contains 256 threads and maps naturally to a two-dimensional image tile.
        const dim3 block(16, 16);
        const dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
        rgb_to_grayscale_kernel<<<grid, block>>>(rgb_d, gray_d, width, height);
        check_cuda(cudaGetLastError(), "launch rgb_to_grayscale_kernel");
        check_cuda(cudaDeviceSynchronize(), "execute rgb_to_grayscale_kernel");
        check_cuda(cudaMemcpy(gray_gpu.data(), gray_d, gray_bytes, cudaMemcpyDeviceToHost), "copy grayscale D2H");
        check_cuda(cudaFree(rgb_d), "cudaFree RGB");
        check_cuda(cudaFree(gray_d), "cudaFree grayscale");

        const int maximum_difference = maximum_byte_difference(gray_gpu, gray_reference);
        png_io::write_grayscale_png(argv[2], gray_gpu, width, height);

        std::cout << "Input: " << argv[1] << " (" << width << 'x' << height << ")\n" << "Block: " << block.x << 'x' << block.y << ", grid: " << grid.x << 'x' << grid.y << '\n'
                  << "Pixels checked against CPU reference: " << pixels << '\n' << "Output: " << argv[2] << '\n'
                  << "Maximum CPU/GPU difference: " << maximum_difference << '\n';

        return maximum_difference == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
