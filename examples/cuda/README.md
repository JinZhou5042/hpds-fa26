# CUDA Examples

CRC front ends can compile CUDA programs but do not have GPUs. Run the programs
on a laptop or workstation with a compatible NVIDIA GPU, or submit them manually
to a CRC GPU worker. Condor submit files are intentionally not provided.

Load CUDA on CRC:

```sh
source /software/Modules/5.6.1/init/bash
module load cuda/12.1
```

Each topic has its own Makefile:

```sh
cd 01-cuda-programming-model
make                         # build everything in this directory
make 1.2_kernel_launch       # build one program
make clean
```

Executables are created in the same directory as the source files. Run them on
a GPU machine, for example:

```sh
./1.2_kernel_launch
```

## Topics

- `01-cuda-programming-model`: kernels, indexing, memory, and correctness
- `02-multidimensional-data`: images and matrix multiplication
- `03-gpu-execution-model`: blocks, warps, synchronization, and occupancy
- `04-memory-locality-and-tiling`: shared memory and tiling

Each directory also contains `overall.cu`, which combines that topic's examples.
