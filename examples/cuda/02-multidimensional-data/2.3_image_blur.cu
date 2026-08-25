/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make 2.3_image_blur
 *   ./2.3_image_blur bird.png bird_blurred.png 2
 *
 * Section 2.3: Blur a PNG with neighborhood boundary conditions
 *
 * This program blurs one grayscale image; it is not a grayscale-to-blur
 * pipeline. png_io.h converts RGB input on the host, so the CPU and GPU receive
 * the same one-byte-per-pixel array.
 *
 * A one-thread-per-output mapping does not require one-input-per-output. Each
 * thread loops over a square neighborhood and averages its valid pixels.
 *
 * Two boundary checks matter:
 *
 * 1. Is this thread's output (row,col) inside the image?
 * 2. Is each candidate neighbor (neighbor_row,neighbor_col) inside the image?
 *
 * For radius=1, corners average 4 pixels, non-corner edges average 6, and
 * interior pixels average 9. Counting only valid neighbors avoids dark edges.
 *
 * Command-line arguments:
 *
 * 1. input PNG path;
 * 2. output blurred PNG path;
 * 3. optional blur radius from 0 through 32; the default is 2.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include "png_io.h"

#include <algorithm>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <vector>


int parse_radius(const char* text) {
    char* end = nullptr;
    const long value = std::strtol(text, &end, 10);
    if (*text == '\0' || *end != '\0' || value < 0 || value > 32) {
        throw std::invalid_argument("Blur radius must be an integer from 0 through 32");
    }
    return static_cast<int>(value);
}

__global__ void blur_kernel(const unsigned char* input, unsigned char* output, int width, int height, int radius) {
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    const int row = blockIdx.y * blockDim.y + threadIdx.y;

    if (col < width && row < height) {
        int sum = 0;
        int valid_pixels = 0;

        for (int dy = -radius; dy <= radius; ++dy) {
            for (int dx = -radius; dx <= radius; ++dx) {
                const int neighbor_row = row + dy;
                const int neighbor_col = col + dx;
                if (neighbor_row >= 0 && neighbor_row < height && neighbor_col >= 0 && neighbor_col < width) {
                    sum += input[neighbor_row * width + neighbor_col];
                    ++valid_pixels;
                }
            }
        }

        // valid_pixels cannot be zero because the center pixel is always valid.
        output[row * width + col] = static_cast<unsigned char>(sum / valid_pixels);
    }
}

void blur_cpu(const std::vector<unsigned char>& input, std::vector<unsigned char>& output, int width, int height, int radius) {
    for (int row = 0; row < height; ++row) {
        for (int col = 0; col < width; ++col) {
            int sum = 0;
            int valid_pixels = 0;
            for (int dy = -radius; dy <= radius; ++dy) {
                for (int dx = -radius; dx <= radius; ++dx) {
                    const int neighbor_row = row + dy;
                    const int neighbor_col = col + dx;
                    if (neighbor_row >= 0 && neighbor_row < height && neighbor_col >= 0 && neighbor_col < width) {
                        sum += input[neighbor_row * width + neighbor_col];
                        ++valid_pixels;
                    }
                }
            }
            output[row * width + col] = static_cast<unsigned char>(sum / valid_pixels);
        }
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
    if (argc != 3 && argc != 4) {
        std::cerr << "Usage: " << argv[0] << " INPUT.png OUTPUT.png [RADIUS]\n";
        return EXIT_FAILURE;
    }

    try {
        const int radius = argc == 4 ? parse_radius(argv[3]) : 2;
        int width = 0;
        int height = 0;
        const std::vector<unsigned char> input_h = png_io::read_grayscale_png(argv[1], width, height);
        const std::size_t pixels = static_cast<std::size_t>(width) * height;
        const std::size_t bytes = pixels * sizeof(unsigned char);
        std::vector<unsigned char> cpu_output(pixels);
        std::vector<unsigned char> gpu_output(pixels);

        blur_cpu(input_h, cpu_output, width, height, radius);

        unsigned char* input_d = nullptr;
        unsigned char* output_d = nullptr;
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&input_d), bytes), "cudaMalloc input");
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&output_d), bytes), "cudaMalloc output");
        check_cuda(cudaMemcpy(input_d, input_h.data(), bytes, cudaMemcpyHostToDevice), "copy input H2D");

        const dim3 block(16, 16);
        const dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
        blur_kernel<<<grid, block>>>(input_d, output_d, width, height, radius);
        check_cuda(cudaGetLastError(), "launch blur_kernel");
        check_cuda(cudaDeviceSynchronize(), "execute blur_kernel");
        check_cuda(cudaMemcpy(gpu_output.data(), output_d, bytes, cudaMemcpyDeviceToHost), "copy output D2H");
        check_cuda(cudaFree(input_d), "cudaFree input");
        check_cuda(cudaFree(output_d), "cudaFree output");

        const int maximum_difference = maximum_byte_difference(gpu_output, cpu_output);
        png_io::write_grayscale_png(argv[2], gpu_output, width, height);
        std::cout << "Input: " << argv[1] << " (" << width << 'x' << height << ")\n" << "Blur radius: " << radius << '\n'
                  << "Block: " << block.x << 'x' << block.y << ", grid: " << grid.x << 'x' << grid.y << '\n' << "Output: " << argv[2] << '\n'
                  << "Pixels checked against CPU reference: " << pixels << '\n' << "Maximum CPU/GPU difference: " << maximum_difference << '\n';

        return maximum_difference == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
