# Course Projects

This directory contains the candidate projects for HPDS. Each project entry
keeps the source reference, available input data, reproducible scripts, and a
small set of baseline results together.

Clone the course repository with its pinned upstream code:

```bash
git clone --recurse-submodules https://github.com/dthain/hpds-fa26.git
```

For an existing checkout, initialize the code links with:

```bash
git submodule update --init --recursive
```

## Material inventory

| Project | Code | Data | Scripts | Baseline results |
| --- | --- | --- | --- | --- |
| [CM1LP](cm1lp/) | Git submodule, `codex-branch` at `2cc680c` | Owner verification namelist | CRC build and 128-rank run | Yes |
| [PyFlowCL](pyflowcl/) | Owner snapshot `98db688ae5f4` | Included HDF5 input and three manuals | Environment setup and smoke test | Yes |
| [MFDn Transitions](mfdn-transitions/) | Git submodule at `dbe217c` | Upstream example | CRC build and MPI/OpenMP run | Yes |
| [QTL Workflow](qtl-workflow/) | Owner R script | QTL CSVs and full VCF | Minimal run, 1,000 permutations, VCF restore | Yes |
| [GBCF nf-core RNA-seq](gbcf-nf-core-rnaseq/) | Git submodule, release 3.26.0 at `e7ca462` | Upstream test profile downloads | Container prefetch and CRC launchers | Yes |
| [BSA and Variant Analysis](bsa-variant-analysis/) | [Owner GitHub repository](https://github.com/NirjharBhattacharyya/Bulk_Segregation_Analysis_Ferdig_Lab) at `24aa27e` | 26.7 MB SNP table | Grid Engine and HTCondor launchers | Yes |
| [NA61 ROOT Analysis](na61-root-analysis/) | Not yet supplied | Not yet supplied | Not yet supplied | No |
| [Subgraph Isomorphism](subgraph-isomorphism/) | Not yet supplied | Not yet supplied | Not yet supplied | No |
| [Persistent Homology / TDA](persistent-homology/) | No implementation selected | Not yet supplied | Not yet supplied | No |

GitHub-hosted upstream projects are referenced rather than duplicated. The
three submodules are pinned to the revisions used for validation. PyFlowCL is
included directly because the supplied snapshot has no public upstream URL.

The QTL VCF exceeds GitHub's per-file limit even after gzip compression. It is
stored as two checked, lossless parts under `qtl-workflow/data/`. Run
`qtl-workflow/scripts/restore-vcf.sh` to reconstruct the original VCF.

Bharat Mishra has several interesting large datasets for the GBCF nf-core
RNA-seq pipeline and will share one through the CRC shared file system when
ready, in place of the built-in test profile currently listed above.

## Contacts

- CM1LP: David Richter (`David.Richter.26@nd.edu`)
- PyFlowCL: Jonathan MacArt (`jmacart@nd.edu`)
- MFDn Transitions: Mark Caprio (`mcaprio@nd.edu`)
- QTL Workflow: Tarrick Qahash (`tqahash@nd.edu`)
- GBCF nf-core RNA-seq: Bharat Mishra (`bmishra2@nd.edu`)
- BSA and Variant Analysis: Nirjhar Bhattacharyya (`nbhattac@nd.edu`)
- NA61 ROOT Analysis: Michael Quintieri (`mquintie@nd.edu`) and Laura Fields (`lfields2@nd.edu`)
- Subgraph Isomorphism and Persistent Homology: Peter Kogge (`Peter.M.Kogge.1@nd.edu`)
