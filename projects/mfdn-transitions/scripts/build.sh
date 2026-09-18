#!/usr/bin/env bash
# Build the pinned MFDn Transitions submodule on a CRC front end.
set -euo pipefail

project_dir=$(cd "$(dirname "$0")/.." && pwd)
module purge
module load intel/24.2 intelmpi/21.13 gsl/gcc/2.8
cmake -S "$project_dir/code" -B "$project_dir/build" \
    -DCMAKE_Fortran_COMPILER=mpiifx
cmake --build "$project_dir/build" --parallel 4
