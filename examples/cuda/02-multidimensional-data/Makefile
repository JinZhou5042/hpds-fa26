.PHONY: all clean

all: 2.1_multidimensional_indices 2.2_rgb_to_grayscale \
	2.3_image_blur 2.4_matrix_multiplication overall

2.1_multidimensional_indices: 2.1_multidimensional_indices.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 2.1_multidimensional_indices.cu -o 2.1_multidimensional_indices

2.2_rgb_to_grayscale: 2.2_rgb_to_grayscale.cu png_io.h ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 2.2_rgb_to_grayscale.cu -lpng -lz -o 2.2_rgb_to_grayscale

2.3_image_blur: 2.3_image_blur.cu png_io.h ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 2.3_image_blur.cu -lpng -lz -o 2.3_image_blur

2.4_matrix_multiplication: 2.4_matrix_multiplication.cu ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 2.4_matrix_multiplication.cu -o 2.4_matrix_multiplication

overall: overall.cu png_io.h ../common/cuda_helpers.h
	nvcc -O3 -std=c++17 overall.cu -lpng -lz -o overall

clean:
	rm -f 2.1_multidimensional_indices 2.2_rgb_to_grayscale \
		2.3_image_blur 2.4_matrix_multiplication overall \
		bird_grayscale.png bird_blurred.png \
		overall_bird_grayscale.png overall_bird_blurred.png
