#!/bin/bash
#SBATCH --account=SLURM_ACCOUNT_FROM_MYBALANCE
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:01:00
#SBATCH --job-name=hpds-warmup
#SBATCH --output=anvil-%j.out

echo "system=anvil"
echo "job_id=${SLURM_JOB_ID}"
echo "user=$(whoami)"
echo "compute_host=$(hostname)"
date -u '+utc_time=%Y-%m-%dT%H:%M:%SZ'
