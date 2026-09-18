# BSA and Variant Analysis

- Domain: computational biology and genomics.
- Contact: Nirjhar Bhattacharyya (`nbhattac@nd.edu`).
- Application: an R workflow for bulk segregant analysis (BSA) of a
  *Plasmodium falciparum* genetic cross (MAL31 × KH004). The owner chose this
  BSA workflow over the broader variant-processing alternative.
- Code: [owner GitHub repository](https://github.com/NirjharBhattacharyya/Bulk_Segregation_Analysis_Ferdig_Lab),
  validated at `24aa27e`. Clone it into `code/upstream` as shown
  in `code/README.md`. The owner named `BSA_OPTIMISATION_MAL_KH` as the
  starting script. The repository is private, students will need to ask
  Nirjhar for GitHub access before they can clone it.

## Input data

`data/BSA6.1.multi.MAL31xKH004.SNP.filter.table` (26.7 MB), supplied by the owner,
is in this directory. It is a tab-separated SNP table with `CHROM`, `POS`,
`REF`, and `ALT`, followed by `AD`, `DP`, `GQ`, and `PL` columns for each
sample: 12,803 variants on 14 chromosomes across 114 bulk samples.

## Workflow

The script:

1. reads the SNP table;
2. computes reference-allele frequencies for every sample from allele and
   read depths;
3. sets frequencies with read depth below 20 to missing;
4. removes local outliers with a sliding-window MAD filter (±50 variants,
   cutoff 2 MADs);
5. applies tricube smoothing (100 kb window) separately for each sample and
   chromosome;
6. writes summary tables and plots.

`BSA_OPTIMISATION_MAL_KH` is a saved interactive R session, not a batch
script, so it cannot be run directly. `scripts/run-bsa.R` runs steps 1–6 with the
original functions and parameters, reading its sample lists from the source
file: 114 samples are filtered, and 103 are smoothed. It does not run the
later QTLseqr G′ section, which needs a GitHub-only package and CSV files that
were not supplied, and it draws only one of the figures (`CQ BSA.pdf`).

## Baseline run

Set up once on a CRC front end, from this directory:

```bash
module load R/4.4.0/gcc/11.5.0
mkdir -p .R-library results
export R_LIBS_USER=$PWD/.R-library
Rscript -e 'install.packages(c("dplyr","magrittr","locfit","reshape2","ggplot2"), lib=".R-library", repos="https://cloud.r-project.org")'
# Current Deriv (a doBy dependency) requires R >= 4.5; 4.1.6 builds on R 4.4.
Rscript -e 'install.packages("https://cloud.r-project.org/src/contrib/Archive/Deriv/Deriv_4.1.6.tar.gz", lib=".R-library", repos=NULL, type="source")'
Rscript -e 'install.packages("doBy", lib=".R-library", repos="https://cloud.r-project.org")'
```

Then submit from `crcfe01` or `crcfe02`:

```bash
cd projects/bsa-variant-analysis
qsub scripts/run-bsa.sge
```

The job writes `results/baseline.log` and, in `results/baseline/`, the
intermediate and smoothed allele-frequency CSVs, a per-sample summary,
`CQ BSA.pdf`, `timings.csv`, and `sessionInfo.txt`.

An HTCondor version is also available: `scripts/run-bsa-condor.sh` and
`scripts/run-bsa-condor.submit`, writing to `results/baseline-recheck/`.

## Course fit

The MAD outlier filter takes 86% of the runtime. For each sample it calls
`median()` and `mad()` on a new 101-value window at every position: about
12,700 windows × 114 samples, or 1.45 million calls. The window spans
chromosome boundaries, and the samples are independent. Students can start
with single-node work (incremental or compiled rolling statistics,
vectorization) and parallelism across samples, then scale to more samples,
replicates, window sizes, or permutation runs on CRC. Smoothing, which the
owner expected to be expensive, took only 3.7 s on this dataset.
