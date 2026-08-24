override TOPIC := 02-multidimensional-data
LDLIBS_overall := -lpng -lz
LDLIBS_2.2_rgb_to_grayscale := -lpng -lz
LDLIBS_2.3_image_blur := -lpng -lz
DEFAULT_ARGS_2.2_rgb_to_grayscale = $(CURDIR)/bird.png $(BUILD_DIR)/2.2_bird_grayscale.png
DEFAULT_ARGS_2.3_image_blur = $(CURDIR)/bird.png $(BUILD_DIR)/2.3_bird_blurred.png 2
DEFAULT_ARGS_overall = $(CURDIR)/bird.png $(BUILD_DIR)/overall_bird_grayscale.png $(BUILD_DIR)/overall_bird_blurred.png 2
include ../common/topic.mk
