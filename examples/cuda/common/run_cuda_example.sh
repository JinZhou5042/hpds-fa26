#!/usr/bin/env bash

set -eo pipefail

program=${1:-}
topic_dir=${2:-}
job_id=${3:-}

if [[ -z "$program" || -z "$topic_dir" || -z "$job_id" ]]; then
    echo "Usage: $0 PROGRAM TOPIC_DIR JOB_ID [PROGRAM_ARGUMENTS...]" >&2
    exit 2
fi
shift 3

if [[ ! "$program" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]]; then
    echo "Invalid program name: $program" >&2
    exit 2
fi

if [[ ! "$job_id" =~ ^[0-9]+\.[0-9]+$ ]]; then
    echo "Invalid HTCondor job ID: $job_id" >&2
    exit 2
fi

topic=${topic_dir##*/}
if [[ ! "$topic" =~ ^(01-cuda-programming-model|02-multidimensional-data|03-gpu-execution-model|04-memory-locality-and-tiling)$ || ! -f "$topic_dir/Makefile" ]]; then
    echo "CUDA topic directory is unavailable or invalid: $topic_dir" >&2
    exit 2
fi

export PATH=/usr/local/bin:/usr/bin:/bin:${PATH:-}
source /software/Modules/5.6.1/init/bash
module load cuda/12.1

set -u
cd "$topic_dir"

job_build_dir="$topic_dir/condor/work/$job_id"

echo "HTCondor job: $job_id"
echo "Execution host: $(hostname)"
echo "CUDA compiler: $(nvcc --version | tail -n 1)"
nvidia-smi --query-gpu=name,driver_version,memory.total \
    --format=csv,noheader
echo "Topic: $topic"
echo "Building target: $program"

make --no-print-directory BUILD_DIR="$job_build_dir" "$program"

echo "Running: $job_build_dir/$program $*"
exec "$job_build_dir/$program" "$@"
