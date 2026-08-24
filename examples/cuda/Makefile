.DEFAULT_GOAL := all

TOPICS := 01-cuda-programming-model 02-multidimensional-data \
	03-gpu-execution-model 04-memory-locality-and-tiling

.PHONY: all help clean $(TOPICS)

all: $(TOPICS)

help:
	@echo "make / make all                 Build all topics"
	@echo "make 03-gpu-execution-model     Build one topic"
	@echo "make clean                      Clean all topics"

$(TOPICS):
	$(MAKE) -C $@ --no-print-directory

clean:
	@for topic in $(TOPICS); do $(MAKE) -C $$topic --no-print-directory clean; done
