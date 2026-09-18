For each of these starter projects, we need the following information collected:
- Contact: Prof or grad student who is willing to meet once with students to go over details.
- Name: Name of software or project
- Purpose: A few sentences about the scientific purpose of the software.
- Link to code
- Link to dataset, or instructions if needed.

## Working well with a minimal dataset (5)

- Contact: David Richter (`David.Richter.26@nd.edu`)
  Name: CM1LP
  Purpose: Atmospheric modeling with moving particles (rain, cloud droplets, spray) added to the CM1 solver; Fortran with MPI and OpenACC GPU acceleration.
  Link to code: https://github.com/RichterLab/CM1LP (`codex-branch`)
  Link to dataset: owner-supplied CRC submission script and verification namelist; runs on CRC with 128 MPI ranks (~1026s total), with load imbalance (25%) and MPI communication (22%) as the largest cost categories.

- Contact: Jon MacArt (`jmacart@nd.edu`)
  Name: PyFlowCL
  Purpose: Compressible/incompressible computational fluid dynamics; Python, MPI (mpi4py), PyTorch/GPU offload, selected C++ kernels.
  Link to code: private repository, code shared by email (`master`, revision `98db688ae5f4`); must stay out of the public course repo, access method for matched students still to be confirmed with Jon.
  Link to dataset: none needed for the 2D shear layer verification case (grid built in code); smoke test runs CPU-only, comparing 1 vs 8 threads.

- Contact: Mark Caprio (`mcaprio@nd.edu`)
  Name: MFDn Transitions
  Purpose: Nuclear-physics wave-function transition postprocessing; Fortran with hybrid MPI/OpenMP.
  Link to code: https://github.com/nd-nuclear-theory/mfdn-transitions
  Link to dataset: repository's included `example-transitions-01` case, runs on CRC with 4 MPI ranks x 8 OpenMP threads; output matches the checked-in reference. Mark offered larger "heavy duty" production input; not yet requested.

- Contact: Tarrick Qahash (`tqahash@nd.edu`)
  Name: QTL Workflow
  Purpose: Genetic linkage mapping (QTL) and mutation search in LOD intervals; R (`qtl` / `rqtl2`).
  Link to code: owner-supplied `ClassCode/QTL_Code.R`
  Link to dataset: owner-supplied CSV; minimal run and 1000-permutation run both work, chromosome 7 peak confirmed by Tarrick as expected for chloroquine. Scope still to choose: modernize to `rqtl2`, or parallelize VCF/gene-interval processing (internal decision, not blocked on Tarrick).

- Contact: Bharat Mishra (`bmishra2@nd.edu`)
  Name: GBCF nf-core RNA-seq
  Purpose: NGS pipeline performance, scheduling, and scaling on CRC.
  Link to code: https://github.com/nf-core/rnaseq (3.26.0, commit `e7ca462`)
  Link to dataset: built-in `test` profile only so far (smoke test, ~25 MB), runs end to end on Grid Engine and HTCondor. Bharat has several interesting large datasets and will share one via the CRC shared file system when ready; a specific performance question still needs to come from him.
  Note: FreeCount and Amplicon Explorer (the two smaller GBCF Shiny apps Bharat also offered) were dropped as candidates. Both are thin, similar-shaped R/Shiny stats apps with little real HPC/scaling story, and keeping only nf-core avoids overloading Bharat with three separate student groups.

## Waiting on the owner (4)

- Contact: Nirjhar Bhattacharyya (`nbhattac@nd.edu`)
  Name: BSA and Variant Analysis
  Purpose: Bulk segregant analysis of a *Plasmodium falciparum* genetic cross; R workflow.
  Link to code: private repository `NirjharBhattacharyya/Bulk_Segregation_Analysis_Ferdig_Lab`; owner has data and code, access invite is pending.
  Link to dataset: owner-supplied SNP table already in hand; baseline run shows a clear bottleneck (MAD outlier filter, 86% of runtime).
  Status: have the data, waiting for GitHub repo access.

- Contact: Michael Quintieri (`mquintie@nd.edu`) and Laura Fields (`lfields2@nd.edu`)
  Name: NA61 ROOT Analysis
  Purpose: High-energy physics event analysis for NA61 at CERN and NuMI neutrino-flux estimation; C++/ROOT.
  Link to code: not yet received
  Link to dataset: not yet received
  Status: Michael is seeking approval from his collaboration to share code and data.

- Contact: Peter Kogge (`Peter.M.Kogge.1@nd.edu`)
  Name: Subgraph Isomorphism
  Purpose: Graph subgraph-isomorphism codes comparing an FPGA-oriented system with conventional HPC systems (HPEC 2024).
  Link to code: not yet received
  Link to dataset: not yet received
  Status: no reply despite a couple of follow-ups.

- Contact: Peter Kogge (`Peter.M.Kogge.1@nd.edu`)
  Name: Persistent Homology / TDA
  Purpose: High-performance topological data analysis.
  Link to code: not yet received
  Link to dataset: not yet received
  Status: same silence as Subgraph Isomorphism; also still exploratory (no concrete implementation identified yet).

## Not yet a concrete candidate

- Kevin Lannon (TopEFT or similar) — initial contact made, no project direction has materialized yet.
- Tijana Milenkovic — not heard back from yet.
- Andrew Kennedy — not heard back from yet.
- Tim Weninger — not heard back from yet.
