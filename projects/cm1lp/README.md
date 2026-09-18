# CM1LP

CM1 is an atmospheric model for simulating clouds and storms. The RichterLab
version adds moving particles that represent droplets such as rain, cloud
droplets, or spray. Fortran, parallelized with MPI and with OpenACC for GPUs.

- Contact: David Richter (`David.Richter.26@nd.edu`)
- Code: <https://github.com/RichterLab/CM1LP>, `codex-branch`, pinned as the
  `code/` submodule
- Input: `data/namelist.input`, a 128³ Pi Chamber case

## Minimal run

From this directory on `crcfe01` or `crcfe02`:

```bash
scripts/build.sh
mkdir -p results
qsub scripts/run-baseline.sge
```

`build.sh` compiles with Intel MPI and NetCDF into `build/cm1.exe`. The job
runs on 128 MPI ranks across two nodes and writes to `results/baseline-run/`.
Grid Engine jobs have to be submitted from `crcfe01` or `crcfe02`, not
`condorfe`.
