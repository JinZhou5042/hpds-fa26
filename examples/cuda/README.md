# CUDA Examples

## CRC environment

Run these commands on a CRC login node:

```sh
source /software/Modules/5.6.1/init/bash
module load cuda/12.1
cd examples/cuda
```

The top-level Makefile builds and cleans topics. GPU execution commands run from
a topic directory. The Make rules request one GPU, 4 GB of memory, and a Red Hat
9 execution node.

## Build

```sh
make help
make                              # Build all topics
make 03-gpu-execution-model       # Build one topic
make clean                        # Clean all topics
```

To build one executable:

```sh
cd 03-gpu-execution-model
make 3.3_block_synchronization
```

Local executables are written to the topic's `build/` directory.

## Run with condor_run

Run one executable:

```sh
cd examples/cuda/03-gpu-execution-model
make condor_run build/3.3_block_synchronization
```

Run every executable in the current topic on one GPU allocation:

```sh
make condor_run
```

The programs run sequentially, with a heading printed before each one.

## Submit batch jobs

Submit one executable:

```sh
make condor_submit build/3.3_block_synchronization
```

Submit one job per executable in the current topic:

```sh
make condor_submit
condor_q "$USER"
```

Each submission prints the exact stdout, stderr, and event-log paths. Batch jobs
load CUDA 12.1 and compile in `condor/work/CLUSTER.PROCESS/` before running.

## Output directories

```text
TOPIC/
├── build/     local executables and generated PNG files
└── condor/    batch output, logs, condor_run files, and job work directories
```

Both directories are generated and ignored by Git. `make clean` removes them.
The original `02-multidimensional-data/bird.png` is input data and is preserved.

## Topics

| Directory | Programs | Content |
|---|---|---|
| `01-cuda-programming-model/` | `1.1`–`1.7` | Kernels, indexing, device memory, correctness |
| `02-multidimensional-data/` | `2.1`–`2.4` | Multidimensional grids, PNG processing, matrix multiplication |
| `03-gpu-execution-model/` | `3.1`–`3.5` | SMs, blocks, synchronization, warps, occupancy |
| `04-memory-locality-and-tiling/` | `4.1`–`4.6` | Memory spaces, shared memory, and tiling |

`overall.cu` in each directory combines that topic's examples. GPU timings use
CUDA events around warmed-up kernels and exclude allocation and memory copies
unless the source says otherwise.
