# MFDn Transitions

Postprocessing of nuclear wave functions from MFDn to compute transition
matrix elements. Fortran with hybrid MPI/OpenMP. Production runs read
terabytes of input on hundreds of ranks, and most of the work is close to
embarrassingly parallel, with reductions at the end.

- Contact: Mark Caprio (`mcaprio@nd.edu`)
- Code: <https://github.com/nd-nuclear-theory/mfdn-transitions>, pinned as
  the `code/` submodule
- Input: the repository's small
  [`example-transitions-01`](https://github.com/nd-nuclear-theory/mfdn-transitions/tree/master/doc/examples/example-transitions-01)
  case. Production inputs are much larger, ask Mark if you want one.

## Minimal run

From this directory on a CRC front end:

```bash
scripts/build.sh
mkdir -p results
qsub scripts/mfdn-small-crc.sh
```

The job runs the example on one node with 4 MPI ranks and 8 OpenMP threads
per rank, and writes to `results/run/`. The example ships with reference
output to compare against.
