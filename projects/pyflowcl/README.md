# PyFlowCL

- Domain: compressible and incompressible computational fluid dynamics.
- Contact: Jonathan MacArt (`jmacart@nd.edu`), who is willing to meet with a
  matched student.
- Technical profile: mostly Python, structured 3D meshes, MPI through
  `mpi4py`, PyTorch arrays and GPU offload, plus selected C++ kernels.
- Course fit: exposes concrete computation/communication bottlenecks while
  remaining more approachable than the group's asynchronous unstructured-mesh
  solver.

## Materials from the owner

Jon sent these materials on 2026-09-10; publication permission has since been
confirmed and they are included here:

- `code/`: the supplied `master` snapshot at revision `98db688ae5f4`.
- `data/workstation-setup-pyflow.pdf`: Python environment setup, including
  compiling the pybind module into the pip environment.
- `data/running-pyflowcl.pdf`: how to run PyFlowCL.
- `data/using-paraview.pdf`: visualizing output files in ParaView.

Some links in the PDFs point to the group's internal wiki and are not
reachable, but Jon expects the documents to be sufficient.

## Getting started (from Jon)

- `master` supports nonreacting compressible flows (for example supersonic
  flow over a wedge or cone) and some reacting flows.
- Required: MPI with `mpi4py`, and HDF5 with `h5py`. HYPRE is not needed on
  `master`.
- Example drivers are in `verification/`. Start with
  `verification/shear_layer_2D/`.
- Keep the CFL number printed at run time, `CFL = u * dt / dx`, below 1.0 and
  ideally below 0.5. Lower it by reducing `dt` or refining the grid spacing in
  the driver file.
- Other working branches add features, including incompressible flow. Their
  dominant communication patterns differ, so they pose different HPC
  challenges; Jon is happy to discuss them.

## Running on CRC

No dataset is needed for the 2D shear layer: the driver builds a uniform grid
and initial condition in code. The only data file in the repository is
`verification/isotropic_3D/data_dnsbox_64.h5` (10 MB).

Build a CPU-only environment once, on a front end:

```bash
scripts/setup-env.sh      # creates pyflowcl/env (about 1.3 GB)
```

It loads `python/3.12.13` and `mpich/4.3.2/gcc/11.5.0`, installs PyTorch
2.14.0 (CPU), NumPy, SciPy, Matplotlib, and h5py from PyPI, builds `mpi4py`
against MPICH, and compiles the `solver_cpp` extension. The PyPI h5py has no
MPI-IO, so serial runs write output normally but parallel runs cannot; follow
`data/workstation-setup-pyflow.pdf` to build HDF5 and h5py from source before
MPI scaling work. Jon's group has prebuilt CRC environments, but their activation
instructions are on the internal wiki.

Smoke test, from `crcfe01` or `crcfe02`:

```bash
qsub scripts/run-smoke.sge
```

`scripts/driver_smoke.py` reuses the upstream
`driver_shear_layer_2D_nondimensional.py` configuration but shrinks the grid
from 2048×2048 to 256×256 and the run from 4000 to 100 steps. Override with
`NX1`, `NX2`, and `NSTEPS`. Output goes under `results/smoke/`.

Verified 2026-09-14 on `d12chas` nodes (serial, one MPI rank):

| Threads | Solve time | Per 10 steps |
| --- | --- | --- |
| 1 | 31.9 s | 3.5 s |
| 8 | 24.7 s | 2.7 s |

Both runs kept CFL near 0.223 and wrote 11 HDF5 files with XDMF metadata
(56 MB), one every 10 steps, readable in ParaView. All fields were finite and
evolved from the initial state. The initial condition adds unseeded NumPy
random perturbations, so repeated runs are not bitwise identical. Logs are in
`results/run-smoke-1thread.uge.log` and `results/run-smoke.uge.log`.

## Candidate performance questions

- Blocking communication along directional MPI subcommunicators.
- Cyclic-reduction parallel Thomas algorithm used by the compressible solver;
  its directional filters reduce available SIMD vectorization.
- Hypre pressure-Poisson solve in incompressible mode, including all-to-all
  communication and dominant solver cost. This applies to an incompressible
  branch, not to `master`.

## Project packet

Still to do: build parallel HDF5/h5py and test multi-rank MPI runs, choose a
solver mode and a representative problem size, measure a baseline at that
size, and settle on one deliberately bounded performance question with Jon.
