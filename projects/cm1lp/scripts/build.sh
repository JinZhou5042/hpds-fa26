#!/usr/bin/env bash
# Build the pinned CM1LP submodule on a CRC front end.
set -euo pipefail

project_dir=$(cd "$(dirname "$0")/.." && pwd)
build_dir=${1:-"$project_dir/build"}

module purge
module load intel/24.2 intelmpi/21.13 netcdf/4.9.2/intel/24.2

rm -rf "$build_dir/source"
mkdir -p "$build_dir"
cp -a "$project_dir/code" "$build_dir/source"
rm -rf "$build_dir/source/.git"

cd "$build_dir/source/src"
make clean
make -j4 FC=ifort USE_MPI=true USE_NETCDF=true \
    NETCDFBASE="$(nf-config --prefix)"
cp ../run/cm1.exe "$build_dir/cm1.exe"
sha256sum "$build_dir/cm1.exe"
