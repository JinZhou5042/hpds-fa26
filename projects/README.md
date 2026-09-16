# Course Projects

These are the candidate projects for HPDS this semester. Each one is a real
application, contributed by a Notre Dame researcher or research group, and
the idea is the same in every case: get in, measure how it actually behaves
on the cluster, and make it faster or bigger. Email the contact listed for
each project to set up an intro meeting before you start.

Some of these use code or data that's private, marked "non-public" below.
We're not putting that in this GitHub repo. Once you're matched to the
project, the owner or course staff will hand you the code and data
directly through CRC.

## Ready to start

### CM1LP
Contact: David Richter (`David.Richter.26@nd.edu`)

CM1LP bolts moving particles onto the CM1 atmospheric solver, for things
like rain, cloud droplets, or spray. It's Fortran, MPI, with OpenACC for
GPU acceleration. Code is public at
<https://github.com/RichterLab/CM1LP> (`codex-branch`). A 128-rank run on
CRC finished in about 1,026 seconds, with load imbalance and MPI
communication as the two biggest chunks of that time. That's a decent
place to start looking for a scaling story.

### PyFlowCL
Contact: Jonathan MacArt (`jmacart@nd.edu`)

A compressible/incompressible CFD solver: Python, MPI via mpi4py, PyTorch
arrays with GPU offload. This is the MacArt group's active research code
and it's non-public. Jon asked that it stay out of the course repo, so
he'll hand it to whoever gets matched. A smoke test of the 2D shear layer
case already runs cleanly on CRC, serial and at 8 threads.

### MFDn Transitions
Contact: Mark Caprio (`mcaprio@nd.edu`)

Postprocesses nuclear many-body wave functions into transition matrix
elements. Fortran, hybrid MPI/OpenMP. Public at
<https://github.com/nd-nuclear-theory/mfdn-transitions>. The repo's own
`example-transitions-01` case runs on CRC (4 ranks x 8 threads) and matches
the reference output. Mark has a much bigger production-scale input ready
to hand over once someone's actually working on this.

### QTL Workflow
Contact: Tarrick Qahash (`tqahash@nd.edu`)

Finds QTL peaks and can dig into genes/mutations in the LOD intervals using
VCF and reference-genome data. R. Tarrick shared the code and data
informally, so treat it as non-public. It'll go to the matched student
via CRC. There are two reasonable directions here: modernize the old
workflow to use `rqtl2`, or parallelize the VCF/gene-interval search. A
run on CRC already reproduces the expected chromosome 7 peak (LOD 9.66)
for chloroquine resistance.

### GBCF nf-core RNA-seq
Contact: Bharat Mishra (`bmishra2@nd.edu`)

Runs the nf-core RNA-seq pipeline on CRC: alignment, quantification, QC,
the works. The pipeline itself is a public open-source project
(<https://github.com/nf-core/rnaseq>), not something Bharat wrote, so
there's no issue linking it. What's missing is a real dataset and
reference genome from Bharat. The built-in smoke-test profile already runs
end to end on both Grid Engine and HTCondor, but that's a toy-sized input.
Once the real dataset shows up it'll probably go out over CRC rather than
into this repo.

### BSA and Variant Analysis
Contact: Nirjhar Bhattacharyya (`nbhattac@nd.edu`)

Bulk segregant analysis of a *Plasmodium falciparum* genetic cross: allele
frequencies, outlier filtering, then smoothing to find regions linked to a
phenotype. R, private repository, non-public. It'll be shared with the
matched student via CRC. We have repo access, the code, and a sample
dataset now, and a full run on CRC finishes in about 2.5 minutes. The
sliding-window outlier filter eats most of that time, which looks like a
solid optimization target.

## Materials pending from the owner

### NA61 ROOT Analysis
Contact: Michael Quintieri (`mquintie@nd.edu`), Laura Fields
(`lfields2@nd.edu`)

Event analysis for the NA61 experiment at CERN, also feeds neutrino-flux
estimates for the NuMI beam at Fermilab. C++/ROOT. Michael is still waiting
on his collaboration to sign off on sharing code and data, so nothing's
available yet. Once it is, it'll almost certainly be non-public given
how collaboration data usually works.

### Subgraph Isomorphism
Contact: Peter Kogge (`Peter.M.Kogge.1@nd.edu`)

Graph subgraph-isomorphism codes and datasets, previously used to compare
an FPGA-oriented system against conventional HPC. Nothing's arrived from
Peter yet.

### Persistent Homology / TDA
Contact: Peter Kogge (`Peter.M.Kogge.1@nd.edu`)

An exploratory direction based on persistent-homology work happening in
Peter's group. Still needs a real codebase and dataset before it's a
project someone can actually start.
