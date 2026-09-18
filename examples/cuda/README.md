# CUDA Examples

Each topic has its own Makefile, and executables are created next to the
source files. The build and run steps depend on the cluster: Notre Dame CRC
uses HTCondor, and Purdue Anvil uses Slurm. The header at the top of every
source file gives the exact commands for both.

## HTCondor (Notre Dame CRC)

CRC front ends can compile CUDA programs but do not have GPUs. Run the programs
on a laptop or workstation with a compatible NVIDIA GPU, or submit them manually
to a CRC GPU worker. Condor submit files are intentionally not provided.

Load CUDA on CRC:

```sh
source /software/Modules/5.6.1/init/bash
module load cuda/12.1
```

Build from a topic directory:

```sh
cd 01-cuda-programming-model
make                         # build everything in this directory
make 1.2_kernel_launch       # build one program
make clean
```

Then run the program on a GPU machine, for example:

```sh
./1.2_kernel_launch
```

## Slurm (Purdue Anvil)

Anvil login nodes can compile CUDA programs but do not have GPUs. Build on the
login node, then submit the program to an A100 GPU node with
`common/anvil_gpu.slurm`, which requests one GPU for 10 minutes on the
`gpu-debug` partition under the course GPU account `cis261613-gpu`.

From a topic directory:

```sh
module load modtree/gpu cuda/12.8.0
make
sbatch ../common/anvil_gpu.slurm ./1.2_kernel_launch
```

Program arguments go after the executable:

```sh
sbatch ../common/anvil_gpu.slurm ./2.3_image_blur bird.png bird_blurred.png 2
```

Check the job with `squeue --me`. When it leaves the queue, the output is in
`cuda-example-JOBID.out` in the same directory.

`gpu-debug` allows at most 2 jobs per user in the queue, and a GPU can take a
while to become free. To run several programs, put them in one job:

```sh
sbatch ../common/anvil_gpu.slurm bash -c './4.3_shared_memory && ./4.4_tiled_matrix_multiplication'
```

## Topics

- `01-cuda-programming-model`: kernels, indexing, memory, and correctness
- `02-multidimensional-data`: images and matrix multiplication
- `03-gpu-execution-model`: blocks, warps, synchronization, and occupancy
- `04-memory-locality-and-tiling`: shared memory and tiling

Each directory also contains `overall.cu`, which combines that topic's examples.
