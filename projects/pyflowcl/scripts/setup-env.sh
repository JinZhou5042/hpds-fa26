#!/usr/bin/env bash
# Build a CPU-only Python environment for PyFlowCL on a CRC front end.
#
# Usage: setup-env.sh [env_dir]      (default: pyflowcl/env)
#
# h5py comes from PyPI without MPI-IO, so serial runs work normally but
# parallel runs cannot read or write output (see source/README.md). HYPRE is
# not needed on the master branch.

set -euo pipefail

project_dir=$(cd "$(dirname "$0")/.." && pwd)
env_dir=${1:-$project_dir/env}

if ! type module >/dev/null 2>&1; then
    for f in "${LMOD_PKG:-}/init/bash" "${MODULESHOME:-}/init/bash" \
             /etc/profile.d/lmod.sh /etc/profile.d/modules.sh; do
        [ -f "$f" ] && source "$f" && break
    done
fi
module load python/3.12.13 mpich/4.3.2/gcc/11.5.0

python3 -m venv "$env_dir"
source "$env_dir/bin/activate"

pip install --upgrade pip setuptools wheel
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install numpy scipy matplotlib h5py nvidia-ml-py
MPICC=mpicc pip install --no-binary=mpi4py mpi4py

# Build the C++ solver extension against the installed torch.
cd "$project_dir/code/src/PyFlowCL/Library"
pip install --no-build-isolation .
rm -rf build *.egg-info

python - <<'EOF'
import torch, numpy, scipy, h5py, mpi4py, solver_cpp
print("torch", torch.__version__, "numpy", numpy.__version__,
      "h5py", h5py.__version__, "mpi4py", mpi4py.__version__)
print("solver_cpp", solver_cpp.__file__)
EOF
