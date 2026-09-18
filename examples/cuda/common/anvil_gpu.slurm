#!/bin/bash
# Purdue Anvil GPU job. From a topic directory, after make:
#   sbatch ../common/anvil_gpu.slurm ./1.6_correctness
#SBATCH --job-name=cuda-example
#SBATCH --account=cis261613-gpu
#SBATCH --partition=gpu-debug
#SBATCH --gpus-per-node=1
#SBATCH --time=00:10:00
#SBATCH --output=%x-%j.out

module -q load modtree/gpu cuda/12.8.0
cd "$SLURM_SUBMIT_DIR"
echo "Job $SLURM_JOB_ID on $(hostname), GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
"$@"
