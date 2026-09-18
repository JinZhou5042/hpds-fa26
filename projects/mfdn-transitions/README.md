# MFDn Transitions

- Domain: nuclear-physics wave-function postprocessing.
- Contact: Mark Caprio (`mcaprio@nd.edu`).
- Code: <https://github.com/nd-nuclear-theory/mfdn-transitions>
- Small example: <https://github.com/nd-nuclear-theory/mfdn-transitions/tree/master/doc/examples/example-transitions-01>
- Technical profile: Fortran with hybrid MPI/OpenMP parallelism. Production
  runs may consume terabytes of input and use hundreds of ranks; much of the
  work is nearly embarrassingly parallel with reductions.
- Course fit: evaluate new hardware, investigate data handling and reduction
  costs, and contrast the small reproducible case with realistic scaling.

## Project packet

Record the exact revision, compiler and library environment, small validation
case, appropriately shareable production-scale input, expected outputs,
baseline scaling, resource limits, and a bounded optimization objective.

## Initial validation

The repository's included `example-transitions-01` case was built and run
successfully on CRC using four MPI ranks and eight OpenMP threads
per rank. Its matrix elements matched the checked-in reference output. This
establishes a working student starting point. Meaningful performance work will
need a larger representative input from the project owner.

## Included materials

- `code/`: upstream Git submodule pinned at `dbe217c`.
- `scripts/build.sh`: CRC Intel MPI/GSL build.
- `scripts/mfdn-small-crc.sh`: four-rank, eight-thread-per-rank validation job.
- `results/`: reference run input, logs, matrix element, and result files.

On a CRC front end, run `scripts/build.sh`, then submit from this directory:

```bash
qsub scripts/mfdn-small-crc.sh
```
