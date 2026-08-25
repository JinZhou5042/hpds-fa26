/*
 * From this topic directory:
 *   module load cuda/12.1
 *   make overall
 *   ./overall bird.png overall_bird_grayscale.png overall_bird_blurred.png 2
 *
 * Overall program: Image pipeline plus matrix multiplication
 *
 * This program runs two pieces of work:
 *
 * 1. read an RGB PNG and use a 2D grid to produce grayscale pixels;
 * 2. feed that device-resident grayscale array directly into a blur kernel;
 * 3. write the grayscale and blurred arrays as PNG files;
 * 4. use another 2D grid to multiply rectangular row-major matrices.
 *
 * Unlike Sections 2.2 and 2.3, it keeps the grayscale image on the GPU and feeds
 * it directly to the blur kernel:
 *
 *     PNG -> RGB host bytes -> GPU grayscale -> GPU blur -> output PNGs
 *
 * Default-stream ordering starts blur after grayscale. Keeping gray_d on the
 * device avoids an intermediate D2H and H2D pair. The CPU implementations are
 * correctness references; performance optimization begins in later topics.
 */

#include <cuda_runtime.h>

#include "../common/cuda_helpers.h"

#include "png_io.h"

#include <algorithm>
#include <cmath>
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

__global__ void grayscale_kernel(const unsigned char* rgb, unsigned char* gray, int width, int height) {
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    const int row = blockIdx.y * blockDim.y + threadIdx.y;
    if (row < height && col < width) {
        const int pixel = row * width + col;
        const int rgb_offset = 3 * pixel;
        const unsigned int r = rgb[rgb_offset];
        const unsigned int g = rgb[rgb_offset + 1];
        const unsigned int b = rgb[rgb_offset + 2];
        gray[pixel] = static_cast<unsigned char>((21u * r + 72u * g + 7u * b) / 100u);
    }
}

__global__ void blur_kernel(const unsigned char* input, unsigned char* output, int width, int height, int radius) {
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    const int row = blockIdx.y * blockDim.y + threadIdx.y;
    if (row < height && col < width) {
        int sum = 0;
        int count = 0;
        for (int dy = -radius; dy <= radius; ++dy) {
            for (int dx = -radius; dx <= radius; ++dx) {
                const int neighbor_row = row + dy;
                const int neighbor_col = col + dx;
                if (neighbor_row >= 0 && neighbor_row < height && neighbor_col >= 0 && neighbor_col < width) {
                    sum += input[neighbor_row * width + neighbor_col];
                    ++count;
                }
            }
        }
        output[row * width + col] = static_cast<unsigned char>(sum / count);
    }
}

__global__ void matmul_kernel(const float* a, const float* b, float* c, int m, int k_size, int n) {
    const int col = blockIdx.x * blockDim.x + threadIdx.x;
    const int row = blockIdx.y * blockDim.y + threadIdx.y;
    if (row < m && col < n) {
        float sum = 0.0f;
        for (int k = 0; k < k_size; ++k) {
            sum += a[row * k_size + k] * b[k * n + col];
        }
        c[row * n + col] = sum;
    }
}

void grayscale_and_blur_cpu(const std::vector<unsigned char>& rgb, std::vector<unsigned char>& gray, std::vector<unsigned char>& blurred, int width, int height, int radius) {
    for (std::size_t pixel = 0; pixel < gray.size(); ++pixel) {
        const std::size_t rgb_offset = 3 * pixel;
        const unsigned int r = rgb[rgb_offset];
        const unsigned int g = rgb[rgb_offset + 1];
        const unsigned int b = rgb[rgb_offset + 2];
        gray[pixel] = static_cast<unsigned char>((21u * r + 72u * g + 7u * b) / 100u);
    }
    for (int row = 0; row < height; ++row) {
        for (int col = 0; col < width; ++col) {
            int sum = 0;
            int count = 0;
            for (int dy = -radius; dy <= radius; ++dy) {
                for (int dx = -radius; dx <= radius; ++dx) {
                    const int neighbor_row = row + dy;
                    const int neighbor_col = col + dx;
                    if (neighbor_row >= 0 && neighbor_row < height && neighbor_col >= 0 && neighbor_col < width) {
                        sum += gray[neighbor_row * width + neighbor_col];
                        ++count;
                    }
                }
            }
            blurred[row * width + col] = static_cast<unsigned char>(sum / count);
        }
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

int maximum_byte_difference(const std::vector<unsigned char>& actual, const std::vector<unsigned char>& expected) {
    int maximum = 0;
    for (std::size_t i = 0; i < actual.size(); ++i) {
        maximum = std::max(maximum, std::abs(static_cast<int>(actual[i]) - static_cast<int>(expected[i])));
    }
    return maximum;
}

int main(int argc, char** argv) {
    if (argc != 4 && argc != 5) {
        std::cerr << "Usage: " << argv[0] << " INPUT.png GRAYSCALE.png BLURRED.png [RADIUS]\n";
        return EXIT_FAILURE;
    }

    try {
        const int radius = argc == 5 ? parse_radius(argv[4]) : 2;
        int width = 0;
        int height = 0;
        const std::vector<unsigned char> rgb_h = png_io::read_rgb_png(argv[1], width, height);
        const std::size_t pixels = static_cast<std::size_t>(width) * height;
        const std::size_t rgb_bytes = 3 * pixels;
        const std::size_t gray_bytes = pixels;
        std::vector<unsigned char> gray_reference(pixels);
        std::vector<unsigned char> blur_reference(pixels);
        std::vector<unsigned char> gray_gpu(pixels);
        std::vector<unsigned char> blur_gpu(pixels);

        grayscale_and_blur_cpu(rgb_h, gray_reference, blur_reference, width, height, radius);

        unsigned char* rgb_d = nullptr;
        unsigned char* gray_d = nullptr;
        unsigned char* blur_d = nullptr;
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&rgb_d), rgb_bytes), "cudaMalloc RGB");
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&gray_d), gray_bytes), "cudaMalloc grayscale");
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&blur_d), gray_bytes), "cudaMalloc blur");
        check_cuda(cudaMemcpy(rgb_d, rgb_h.data(), rgb_bytes, cudaMemcpyHostToDevice), "copy RGB H2D");

        const dim3 image_block(16, 16);
        const dim3 image_grid((width + image_block.x - 1) / image_block.x, (height + image_block.y - 1) / image_block.y);
        grayscale_kernel<<<image_grid, image_block>>>(rgb_d, gray_d, width, height);
        check_cuda(cudaGetLastError(), "launch grayscale_kernel");
        blur_kernel<<<image_grid, image_block>>>(gray_d, blur_d, width, height, radius);
        check_cuda(cudaGetLastError(), "launch blur_kernel");
        check_cuda(cudaDeviceSynchronize(), "execute image pipeline");
        check_cuda(cudaMemcpy(gray_gpu.data(), gray_d, gray_bytes, cudaMemcpyDeviceToHost), "copy grayscale D2H");
        check_cuda(cudaMemcpy(blur_gpu.data(), blur_d, gray_bytes, cudaMemcpyDeviceToHost), "copy blur D2H");
        check_cuda(cudaFree(rgb_d), "cudaFree RGB");
        check_cuda(cudaFree(gray_d), "cudaFree grayscale");
        check_cuda(cudaFree(blur_d), "cudaFree blur");

        const int gray_difference = maximum_byte_difference(gray_gpu, gray_reference);
        const int blur_difference = maximum_byte_difference(blur_gpu, blur_reference);
        png_io::write_grayscale_png(argv[2], gray_gpu, width, height);
        png_io::write_grayscale_png(argv[3], blur_gpu, width, height);

        std::cout << "Image pipeline: " << argv[1] << " (" << width << 'x' << height << "), blur radius: " << radius << '\n'
                  << "Grayscale output: " << argv[2] << '\n' << "Blurred output: " << argv[3] << '\n'
                  << "Device-resident handoff: grayscale output feeds blur without an intermediate host copy.\n"
                  << "Pixels checked against CPU references: " << pixels << '\n'
                  << "Maximum grayscale difference: " << gray_difference << '\n' << "Maximum blur difference: " << blur_difference << '\n';

        // Use a substantial rectangular problem whose dimensions also exercise the 16x16 grid's boundary guards.
        const int m = 513;
        const int k_size = 511;
        const int n = 515;
        std::vector<float> a_h(m * k_size);
        std::vector<float> b_h(k_size * n);
        std::vector<float> c_reference(m * n);
        std::vector<float> c_gpu(m * n);
        for (std::size_t i = 0; i < a_h.size(); ++i) {
            a_h[i] = static_cast<float>(i % 11) * 0.25f;
        }
        for (std::size_t i = 0; i < b_h.size(); ++i) {
            b_h[i] = static_cast<float>(i % 13) * 0.125f - 0.5f;
        }

        matmul_cpu(a_h, b_h, c_reference, m, k_size, n);

        float* a_d = nullptr;
        float* b_d = nullptr;
        float* c_d = nullptr;
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&a_d), a_h.size() * sizeof(float)), "cudaMalloc A");
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&b_d), b_h.size() * sizeof(float)), "cudaMalloc B");
        check_cuda(cudaMalloc(reinterpret_cast<void**>(&c_d), c_gpu.size() * sizeof(float)), "cudaMalloc C");
        check_cuda(cudaMemcpy(a_d, a_h.data(), a_h.size() * sizeof(float), cudaMemcpyHostToDevice), "copy A H2D");
        check_cuda(cudaMemcpy(b_d, b_h.data(), b_h.size() * sizeof(float), cudaMemcpyHostToDevice), "copy B H2D");

        const dim3 matrix_block(16, 16);
        const dim3 matrix_grid((n + matrix_block.x - 1) / matrix_block.x, (m + matrix_block.y - 1) / matrix_block.y);
        matmul_kernel<<<matrix_grid, matrix_block>>>(a_d, b_d, c_d, m, k_size, n);
        check_cuda(cudaGetLastError(), "launch matmul_kernel");
        check_cuda(cudaDeviceSynchronize(), "execute matmul_kernel");
        check_cuda(cudaMemcpy(c_gpu.data(), c_d, c_gpu.size() * sizeof(float), cudaMemcpyDeviceToHost), "copy C D2H");
        check_cuda(cudaFree(a_d), "cudaFree A");
        check_cuda(cudaFree(b_d), "cudaFree B");
        check_cuda(cudaFree(c_d), "cudaFree C");

        float matrix_max_error = 0.0f;
        for (std::size_t i = 0; i < c_gpu.size(); ++i) {
            matrix_max_error = std::max(matrix_max_error, std::fabs(c_gpu[i] - c_reference[i]));
        }
        std::cout << "Matrix: " << m << 'x' << k_size << " times " << k_size << 'x' << n << '\n'
                  << "Outputs checked against CPU reference: " << c_gpu.size() << '\n' << "Maximum absolute error: " << matrix_max_error << '\n';

        return gray_difference == 0 && blur_difference == 0 && matrix_max_error <= 1.0e-4f ? EXIT_SUCCESS : EXIT_FAILURE;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
