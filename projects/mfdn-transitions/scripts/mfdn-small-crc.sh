#!/bin/bash

#$ -cwd
#$ -pe mpi-64 64
#$ -N mfdn_small
#$ -j y
#$ -o results/sge.log

set -uo pipefail

project_root="${SGE_O_WORKDIR:?submit from the MFDn project directory}"
run_dir="$project_root/results/run"
work_dir="$run_dir/work"

echo "job_id=${JOB_ID:-unknown}"
echo "start_time=$(date --iso-8601=seconds)"
echo "submit_host=${SGE_O_HOST:-unknown}"
echo "execution_host=$(hostname -f)"
echo "run_dir=$run_dir"
echo "nslots=${NSLOTS:-unset}"

module purge
module load intel/24.2
module load intelmpi/21.13
module load gsl/gcc/2.8
module list

if [[ "${NSLOTS:-0}" -ne 64 ]]; then
    echo "ERROR: expected one 64-slot node, received ${NSLOTS:-unset}" >&2
    exit 2
fi

if [[ ! -x "$project_root/build/xtransitions" ]]; then
    echo "ERROR: xtransitions is missing" >&2
    exit 2
fi

mkdir -p "$work_dir"
ln -sfn "$project_root/code/doc/examples/data" "$run_dir/data"
cp "$project_root/code/doc/examples/example-transitions-01/transitions.input" "$work_dir/transitions.input"
rm -f "$work_dir"/transitions.res "$work_dir"/transitions.robdme.*

cd "$work_dir" || exit 2
export OMP_NUM_THREADS=8

echo "launch_time=$(date --iso-8601=seconds)"
mpirun -np 4 "$project_root/build/xtransitions" > stdout.log 2> stderr.log
status=$?
echo "finish_time=$(date --iso-8601=seconds)"
echo "xtransitions_exit_status=$status"

if [[ "$status" -ne 0 ]]; then
    exit "$status"
fi

if [[ ! -s transitions.res ]] || ! compgen -G 'transitions.robdme.*' >/dev/null; then
    echo "ERROR: expected output files were not produced" >&2
    exit 3
fi

echo "output_files:"
sha256sum transitions.res transitions.robdme.*
