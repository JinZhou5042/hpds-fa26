# Shared build rules for one learning topic.
# The including Makefile must set TOPIC before including this file.

CXX := g++
NVCC := nvcc
# Use known teaching defaults even when a Conda environment exports unrelated
# compiler flags. A command-line override still works, for example:
# make NVCCFLAGS='-O0 -g -G -std=c++17'
CXXFLAGS := -O2 -std=c++17 -Wall -Wextra
NVCCFLAGS := -O3 -std=c++17 -Xcompiler=-Wall,-Wextra

CUDA_DIR := $(abspath ..)
BUILD_DIR ?= $(CURDIR)/build
PROGRAM ?=
GOAL_EXECUTABLES = $(filter build/%,$(MAKECMDGOALS))
INVALID_CONDOR_GOALS = $(filter-out condor_run condor_submit build/%,$(MAKECMDGOALS))
PROGRAM_PATH = $(patsubst ./%,%,$(strip $(if $(PROGRAM),$(PROGRAM),$(firstword $(GOAL_EXECUTABLES)))))
PROGRAM_NAME = $(notdir $(PROGRAM_PATH))
PROGRAM_ARGS = $(strip $(DEFAULT_ARGS_$(PROGRAM_NAME)))
FOLDER_RUN_COMMAND = set -e; $(foreach program,$(PROGRAMS),printf "\n========== %s ==========\n" $(program); $(BUILD_DIR)/$(program) $(DEFAULT_ARGS_$(program));)

CPP_SOURCES := $(wildcard *.cpp)
CUDA_SOURCES := $(wildcard *.cu)
PROGRAMS := $(notdir $(basename $(CPP_SOURCES) $(CUDA_SOURCES)))
BINARIES := $(addprefix $(BUILD_DIR)/,$(PROGRAMS))
EXECUTABLE_TARGETS := $(addprefix build/,$(PROGRAMS))
CONDOR_DIR := $(CURDIR)/condor

.DEFAULT_GOAL := all
.PHONY: all help condor_run condor_submit _condor_run_one _condor_submit_one clean $(PROGRAMS)
.DELETE_ON_ERROR:

all: $(BINARIES)

help:
	@echo "make / make all                         Build every program in this topic"
	@echo "make condor_run [build/NAME]            Run one executable or this whole topic"
	@echo "make condor_submit [build/NAME]         Submit one executable or this whole topic"
	@echo "make clean                              Remove generated outputs"

$(PROGRAMS): %: $(BUILD_DIR)/%
	@:

$(EXECUTABLE_TARGETS): build/%: %
	@:

$(BUILD_DIR)/%: %.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $< -o $@

$(BUILD_DIR)/%: %.cu | $(BUILD_DIR)
	$(NVCC) $(NVCCFLAGS) $< -o $@ $(LDLIBS_$*)

condor_run:
	@if [ -n "$(INVALID_CONDOR_GOALS)" ]; then echo "Executable targets must use build/NAME, not '$(INVALID_CONDOR_GOALS)'." >&2; echo "Example: make condor_run build/$(firstword $(PROGRAMS))" >&2; exit 2; fi
	@if [ -n "$(word 2,$(GOAL_EXECUTABLES))" ]; then echo "Choose only one build/NAME executable." >&2; exit 2; fi
	@if [ -n "$(PROGRAM_PATH)" ]; then \
	  make --no-print-directory _condor_run_one PROGRAM='$(PROGRAM_PATH)'; \
	else \
	  make --no-print-directory all; \
	  mkdir -p '$(CONDOR_DIR)'; \
	  cd '$(CONDOR_DIR)' && condor_run -a request_gpus=1 -a request_memory=4GB -a 'requirements=(OpSysAndVer == "RedHat9")' '$(FOLDER_RUN_COMMAND)'; \
	fi

condor_submit:
	@if [ -n "$(INVALID_CONDOR_GOALS)" ]; then echo "Executable targets must use build/NAME, not '$(INVALID_CONDOR_GOALS)'." >&2; echo "Example: make condor_submit build/$(firstword $(PROGRAMS))" >&2; exit 2; fi
	@if [ -n "$(word 2,$(GOAL_EXECUTABLES))" ]; then echo "Choose only one build/NAME executable." >&2; exit 2; fi
	@if [ -n "$(PROGRAM_PATH)" ]; then \
	  make --no-print-directory _condor_submit_one PROGRAM='$(PROGRAM_PATH)'; \
	else \
	  set -e; for program in $(PROGRAMS); do \
	    make --no-print-directory _condor_submit_one PROGRAM="build/$$program"; \
	  done; \
	fi

_condor_run_one:
	@case "$(PROGRAM_PATH)" in \
	  build/*/*|build/) echo "PROGRAM must identify one executable directly under build/." >&2; \
	     echo "Example: make condor_run build/$(firstword $(PROGRAMS))" >&2; exit 2 ;; \
	  build/*) ;; \
	  *) echo "Select an executable with a build/NAME Make target, not '$(PROGRAM)'." >&2; \
	     echo "Example: make condor_run build/$(firstword $(PROGRAMS))" >&2; exit 2 ;; \
	esac
	@case " $(PROGRAMS) " in \
	  *" $(PROGRAM_NAME) "*) ;; \
	  *) echo "Unknown executable '$(PROGRAM_PATH)' in topic '$(TOPIC)'." >&2; \
	     echo "Available executables: $(addprefix build/,$(PROGRAMS))" >&2; exit 2 ;; \
	esac
	@$(MAKE) --no-print-directory $(PROGRAM_NAME)
	@mkdir -p '$(CONDOR_DIR)'; \
	command='$(BUILD_DIR)/$(PROGRAM_NAME) $(PROGRAM_ARGS)'; \
	cd '$(CONDOR_DIR)' && condor_run -a request_gpus=1 -a request_memory=4GB -a 'requirements=(OpSysAndVer == "RedHat9")' "$$command"

_condor_submit_one:
	@case "$(PROGRAM_PATH)" in \
	  build/*/*|build/) echo "PROGRAM must identify one executable directly under build/." >&2; \
	     echo "Example: make condor_submit build/$(firstword $(PROGRAMS))" >&2; exit 2 ;; \
	  build/*) ;; \
	  *) echo "Select an executable with a build/NAME Make target, not '$(PROGRAM)'." >&2; \
	     echo "Example: make condor_submit build/$(firstword $(PROGRAMS))" >&2; exit 2 ;; \
	esac
	@case " $(PROGRAMS) " in \
	  *" $(PROGRAM_NAME) "*) ;; \
	  *) echo "Unknown executable '$(PROGRAM_PATH)' in topic '$(TOPIC)'." >&2; \
	     echo "Available executables: $(addprefix build/,$(PROGRAMS))" >&2; exit 2 ;; \
	esac
	@set -e; \
	batch_name='$(TOPIC)-$(PROGRAM_NAME)'; \
	mkdir -p $(CONDOR_DIR) $(CONDOR_DIR)/work; \
	job_range=$$(condor_submit -terse \
		-batch-name "$$batch_name" \
		-append 'program = $(PROGRAM_NAME)' \
		-append 'topic_dir = $(CURDIR)' \
		-append 'program_args = $(PROGRAM_ARGS)' \
		$(CUDA_DIR)/common/cuda_gpu.sub); \
	job_id=$${job_range%% *}; \
	case "$$job_id" in ''|*[!0-9.]*) echo "Could not parse submitted job ID from: $$job_range" >&2; exit 2 ;; esac; \
	echo "Submitted job $$job_id"; \
	echo "  stdout: $(CONDOR_DIR)/$(PROGRAM_NAME).$$job_id.out"; \
	echo "  stderr: $(CONDOR_DIR)/$(PROGRAM_NAME).$$job_id.err"; \
	echo "  log:    $(CONDOR_DIR)/$(PROGRAM_NAME).$$job_id.log"

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -rf -- $(BUILD_DIR)
	rm -rf -- $(CONDOR_DIR)
	rm -f -- $(PROGRAMS)
