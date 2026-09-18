# CM1LP

- Domain: atmospheric modeling and particle-laden flow.
- Contact: David Richter (`David.Richter.26@nd.edu`).
- Code: <https://github.com/RichterLab/CM1LP>
- Technical profile: Fortran atmospheric solver using MPI and OpenACC with
  GPU acceleration. The RichterLab version adds moving particles representing
  droplets such as rain, cloud droplets, or spray.
- Course fit: compare hardware or GPU behavior, measure MPI/OpenACC scaling,
  locate bottlenecks, or evaluate alternative parallel strategies.

## Known starting point

The owner identified the repository's `codex-branch` as the intended starting
point. A CRC submission script and verification input were supplied by email.
The portable scripts are in `scripts/`, the input is `data/namelist.input`,
and the pinned upstream source is the `code/` submodule. Its `src` directory contains a
Makefile intended to work with the modules loaded by the submission script.

Grid Engine validation and submission for this project must be run from
`crcfe01.crc.nd.edu` or `crcfe02.crc.nd.edu`. Do not run `qsub` from
`condorfe.crc.nd.edu`; it is not an authorized Grid Engine submit host.

## Running it

The owner's verification case is built from `codex-branch` (commit
`2cc680c`). Build with `scripts/build.sh`, then submit
`scripts/run-baseline.sge` from this directory (128 MPI ranks,
`-pe mpi-64 128`, 64 ranks on each of two hosts). Logs and outputs land in
`results/`.

## Included materials

- `code/`: Git submodule at commit `2cc680c` on `codex-branch`.
- `data/namelist.input`: owner-provided 128³ Pi-chamber configuration.
- `scripts/build.sh`: reproducible Intel MPI/NetCDF build on CRC.
- `scripts/run-baseline.sge`: portable 128-rank Grid Engine job.
- `results/`: module, build, timing, checksum, and compact model evidence.
