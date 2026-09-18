# Course Projects

For each of these starter projects, we need the following information
collected:
- Contact: prof or grad student who is willing to meet once with students to
  go over details.
- Name: name of software or project.
- Purpose: a few sentences about the scientific purpose of the software.
- Link to code.
- Link to dataset, or instructions if needed.

Each project folder keeps the source code, input data, scripts, and baseline
results together.

Clone the course repository with its pinned upstream code:

```bash
git clone --recurse-submodules https://github.com/dthain/hpds-fa26.git
```

For an existing checkout, initialize the code links with:

```bash
git submodule update --init --recursive
```

## Working well with a minimal dataset (5)

- Contact: David Richter (`David.Richter.26@nd.edu`)
  Name: [CM1LP](cm1lp/)
  Purpose: Atmospheric modeling with moving particles (rain, cloud droplets, spray) added to the CM1 solver. Fortran with MPI and OpenACC GPU acceleration.
  Link to code: https://github.com/RichterLab/CM1LP, a git submodule pinned to `codex-branch` at `2cc680c`.
  Link to dataset: owner-supplied CRC submission script and verification namelist. Runs on CRC with 128 MPI ranks (~1026s total), with load imbalance (25%) and MPI communication (22%) as the largest cost categories.
  Scripts and baseline results: CRC build and 128-rank run, done.

- Contact: Jon MacArt (`jmacart@nd.edu`)
  Name: [PyFlowCL](pyflowcl/)
  Purpose: Compressible/incompressible computational fluid dynamics. Python, MPI (mpi4py), PyTorch/GPU offload, selected C++ kernels.
  Link to code: private repository, code shared by email (`master`, revision `98db688ae5f4`), included directly since it has no public upstream URL. Must stay out of the public course repo. The student working on PyFlowCL will contact Jon directly once matched.
  Link to dataset: none needed for the 2D shear layer verification case (grid built in code), plus the included HDF5 input and three manuals.
  Scripts and baseline results: environment setup and a CPU-only smoke test, 1 vs 8 threads, done.

- Contact: Mark Caprio (`mcaprio@nd.edu`)
  Name: [MFDn Transitions](mfdn-transitions/)
  Purpose: Nuclear-physics wave-function transition postprocessing. Fortran with hybrid MPI/OpenMP.
  Link to code: https://github.com/nd-nuclear-theory/mfdn-transitions, a git submodule pinned at `dbe217c`.
  Link to dataset: repository's included `example-transitions-01` case. Mark offered larger "heavy duty" production input, not yet requested.
  Scripts and baseline results: CRC build and a 4 MPI ranks x 8 OpenMP threads run, output matches the checked-in reference.

- Contact: Tarrick Qahash (`tqahash@nd.edu`)
  Name: [QTL Workflow](qtl-workflow/)
  Purpose: Genetic linkage mapping (QTL) and mutation search in LOD intervals. R (`qtl` / `rqtl2`).
  Link to code: owner-supplied `ClassCode/QTL_Code.R`.
  Link to dataset: owner-supplied CSV plus the full VCF. The VCF exceeds GitHub's per-file limit even after gzip, so it's stored as two checked, lossless parts under `qtl-workflow/data/`, run `qtl-workflow/scripts/restore-vcf.sh` to reconstruct it.
  Scripts and baseline results: minimal run and a 1,000-permutation run, both done, chromosome 7 peak confirmed by Tarrick as expected for chloroquine. Still deciding whether to modernize to `rqtl2` or parallelize VCF/gene-interval processing, our call, not something we're waiting on Tarrick for.

- Contact: Bharat Mishra (`bmishra2@nd.edu`)
  Name: [GBCF nf-core RNA-seq](gbcf-nf-core-rnaseq/)
  Purpose: NGS pipeline performance, scheduling, and scaling on CRC.
  Link to code: https://github.com/nf-core/rnaseq, a git submodule pinned to release 3.26.0 at `e7ca462`.
  Link to dataset: upstream `test` profile downloads only so far (smoke test, ~25 MB). Bharat has several interesting large datasets and will share one via the CRC shared file system when ready. A specific performance question still needs to come from him.
  Scripts and baseline results: container prefetch and CRC launchers, runs end to end on Grid Engine and HTCondor.
  Note: dropped Bharat's other two offers, FreeCount and Amplicon Explorer. They're both thin R/Shiny stats apps with little real HPC story, and sticking with just nf-core keeps us from splitting Bharat across three student groups.

## Waiting on the owner (4)

- Contact: Nirjhar Bhattacharyya (`nbhattac@nd.edu`)
  Name: [BSA and Variant Analysis](bsa-variant-analysis/)
  Purpose: Bulk segregant analysis of a *Plasmodium falciparum* genetic cross. R workflow.
  Link to code: [owner's GitHub repository](https://github.com/NirjharBhattacharyya/Bulk_Segregation_Analysis_Ferdig_Lab), pinned at `24aa27e`. Owner has data and code, access invite is pending.
  Link to dataset: owner-supplied SNP table already in hand (26.7 MB). Baseline run shows a clear bottleneck, the MAD outlier filter, 86% of runtime.
  Scripts and baseline results: Grid Engine and HTCondor launchers, done.
  Status: have the data, waiting for GitHub repo access.

- Contact: Michael Quintieri (`mquintie@nd.edu`) and Laura Fields (`lfields2@nd.edu`)
  Name: [NA61 ROOT Analysis](na61-root-analysis/)
  Purpose: High-energy physics event analysis for NA61 at CERN and NuMI neutrino-flux estimation. C++/ROOT.
  Link to code: not yet received.
  Link to dataset: not yet received.
  Status: Michael is seeking approval from his collaboration to share code and data.

- Contact: Peter Kogge (`Peter.M.Kogge.1@nd.edu`)
  Name: [Subgraph Isomorphism](subgraph-isomorphism/)
  Purpose: Graph subgraph-isomorphism codes comparing an FPGA-oriented system with conventional HPC systems (HPEC 2024).
  Link to code: not yet received.
  Link to dataset: not yet received.
  Status: no reply despite a couple of follow-ups.

- Contact: Peter Kogge (`Peter.M.Kogge.1@nd.edu`)
  Name: [Persistent Homology / TDA](persistent-homology/)
  Purpose: High-performance topological data analysis.
  Link to code: no implementation selected yet.
  Link to dataset: not yet received.
  Status: same silence as Subgraph Isomorphism, and still exploratory, no concrete implementation picked yet.
