#!/usr/bin/env bash
# Run the 2D shear layer smoke test in this directory.
#
# Usage: run-smoke.sh
# Environment overrides: NX1, NX2, NSTEPS (driver), OMP_NUM_THREADS.
# Requires the environment built by ../../setup-env.sh.

set -euo pipefail

script_dir=$(cd "$(dirname "$0")" && pwd)
project_dir=$(cd "$script_dir/.." && pwd)
run_dir="$project_dir/results/smoke"

if ! type module >/dev/null 2>&1; then
    for f in "${LMOD_PKG:-}/init/bash" "${MODULESHOME:-}/init/bash" \
             /etc/profile.d/lmod.sh /etc/profile.d/modules.sh; do
        [ -f "$f" ] && source "$f" && break
    done
fi
module load python/3.12.13 mpich/4.3.2/gcc/11.5.0
source "$project_dir/env/bin/activate"

# CRC's default environment already sets OMP_NUM_THREADS, so under Grid Engine
# use the granted slot count instead.
if [ -n "${NSLOTS:-}" ]; then
    export OMP_NUM_THREADS=$NSLOTS
else
    export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1}
fi

mkdir -p "$run_dir"
cd "$run_dir"
echo "host=$(hostname) OMP_NUM_THREADS=$OMP_NUM_THREADS NX1=${NX1:-256} NX2=${NX2:-256} NSTEPS=${NSTEPS:-100}"
exec python -u "$script_dir/driver_smoke.py"
