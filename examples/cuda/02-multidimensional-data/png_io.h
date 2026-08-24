#pragma once

/*
 * Small host-only PNG I/O helper used by the image lessons in this directory.
 *
 * PNG files are compressed and may use several channel layouts. CUDA kernels
 * should not need to understand that file format. These functions ask
 * libpng's simplified API to decode a PNG into an ordinary row-major byte
 * array before CUDA sees it, or encode such an array after CUDA finishes.
 *
 * read_rgb_png:       returns R, G, B, R, G, B, ... (three bytes per pixel).
 * read_grayscale_png: returns one intensity byte per pixel.
 * write_grayscale_png writes one intensity byte per pixel as a grayscale PNG.
 */

#include <png.h>

#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace png_io {

inline std::vector<unsigned char> read_png_as(const char* path, int& width, int& height, png_uint_32 format) {
    png_image image{};
    image.version = PNG_IMAGE_VERSION;

    if (!png_image_begin_read_from_file(&image, path)) {
        throw std::runtime_error(std::string("Cannot open input PNG: ") + image.message);
    }
    if (image.width > static_cast<png_uint_32>(std::numeric_limits<int>::max()) || image.height > static_cast<png_uint_32>(std::numeric_limits<int>::max())) {
        png_image_free(&image);
        throw std::runtime_error("Image dimensions exceed the integer range used by the CUDA kernels");
    }

    image.format = format;
    std::vector<unsigned char> pixels(PNG_IMAGE_SIZE(image));
    if (!png_image_finish_read(&image, nullptr, pixels.data(), 0, nullptr)) {
        const std::string message = image.message;
        png_image_free(&image);
        throw std::runtime_error(std::string("Cannot decode input PNG: ") + message);
    }

    width = static_cast<int>(image.width);
    height = static_cast<int>(image.height);
    png_image_free(&image);
    return pixels;
}

inline std::vector<unsigned char> read_rgb_png(const char* path, int& width, int& height) {
    return read_png_as(path, width, height, PNG_FORMAT_RGB);
}

inline std::vector<unsigned char> read_grayscale_png(const char* path, int& width, int& height) {
    return read_png_as(path, width, height, PNG_FORMAT_GRAY);
}

inline void write_grayscale_png(const char* path, const std::vector<unsigned char>& pixels, int width, int height) {
    if (width <= 0 || height <= 0 || pixels.size() != static_cast<std::size_t>(width) * height) {
        throw std::invalid_argument("Grayscale PNG dimensions do not match its pixel array");
    }

    png_image image{};
    image.version = PNG_IMAGE_VERSION;
    image.width = static_cast<png_uint_32>(width);
    image.height = static_cast<png_uint_32>(height);
    image.format = PNG_FORMAT_GRAY;

    if (!png_image_write_to_file(&image, path, 0, pixels.data(), 0, nullptr)) {
        throw std::runtime_error(std::string("Cannot write output PNG: ") + image.message);
    }
}

}  // namespace png_io
