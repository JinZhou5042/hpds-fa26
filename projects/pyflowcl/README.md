# PyFlowCL

Compressible and incompressible CFD on structured 3D meshes. Mostly Python,
with MPI through `mpi4py`, PyTorch arrays on CPU or GPU, and a few C++
kernels.

- Contact: Jon MacArt (`jmacart@nd.edu`)
- Code: `code/`, a snapshot of the `master` branch. There is no public
  repository.
- Guides: `data/workstation-setup-pyflow.pdf` (environment),
  `data/running-pyflowcl.pdf` (running), `data/using-paraview.pdf` (viewing
  output). Some links in them point to the group's internal wiki.

## Getting started

- `master` supports nonreacting compressible flows (for example supersonic
  flow over a wedge or cone) and some reacting flows. Other branches add
  features such as incompressible flow. Ask Jon if you want to work with them.
- You need MPI with `mpi4py` and HDF5 with `h5py`.
- Example cases are in `code/verification/`. `shear_layer_2D` is a good first
  one and needs no input data.
- Keep the CFL number printed at run time below 1, ideally below 0.5, by
  reducing `dt` or refining the grid.

## Minimal run

Build a CPU-only environment once, from this directory on a CRC front end:

```bash
scripts/setup-env.sh
```

It installs `h5py` from PyPI, which has no MPI-IO, so only single-rank runs
can write output. Build HDF5 and `h5py` from source (see the setup guide)
before running on multiple ranks.

Then submit the smoke test from `crcfe01` or `crcfe02`:

```bash
mkdir -p results
qsub scripts/run-smoke.sge
```

`scripts/driver_smoke.py` is the 2D shear layer shrunk to 256×256 and 100
steps. Change the size with `NX1`, `NX2`, and `NSTEPS`. Output goes to
`results/smoke/` and opens in ParaView. The initial condition uses unseeded
random perturbations, so runs are not bitwise identical.
