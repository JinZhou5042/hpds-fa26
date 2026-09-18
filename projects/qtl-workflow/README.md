# QTL Workflow

- Domain: genetic linkage mapping and variant interpretation.
- Contact: Tarrick Qahash (`tqahash@nd.edu`).
- Technical profile: R-based multiple-QTL modeling and/or a workflow that
  finds QTL peaks, searches genes in LOD intervals, and examines mutations
  using VCF and reference-genome data.

## Included materials

- `code/QTL_Code.R`: original owner-supplied analysis.
- `data/*.csv`: linkage-map and phenotype inputs.
- `data/hb3_dd2.gatk.final.vcf.gz.part-*`: complete owner VCF as two lossless
  parts. Run `scripts/restore-vcf.sh` to reconstruct it and verify both hashes.
- `scripts/`: repeatable smoke and permutation analyses.
- `results/`: checked outputs and logs from the CRC validation.

## Minimal run

From this directory on CRC:

```bash
module load R/4.4.0/gcc/11.5.0
mkdir -p .R-library
Rscript -e 'install.packages("qtl", lib=".R-library", repos="https://cloud.r-project.org")'
Rscript scripts/minimal-run.R > results/minimal-run.log 2>&1
```

Package installation is only needed once. It uses the supplied
CSV and the original script's second phenotype (`CQ..IC50.`), Haley-Knott
scan, and batch size, with a fixed seed and only 10 permutations.
It reads 37 individuals, 625 markers, and 14 chromosomes and writes
`results/scanone.csv`, `results/permutations.csv`, and
`results/qtl-scan.png`.

The original import treats `N/A` genotype entries as missing. One individual
has no value for this phenotype and is excluded from the scan. Markers on
chromosome 13 include duplicate positions. These warnings are retained in
the log, and the supplied data and original `code/QTL_Code.R` are unchanged.

Ten permutations are only a smoke test, use the run below for the original
permutation count.

## Single-phenotype permutation run

After the environment setup above, run:

```bash
Rscript scripts/permutation-run.R > results/permutation-1000.log 2>&1
```

Uses the same host, R version, package, input,
phenotype, and scan parameters as the minimal run. The seed is 20260907.
Outputs are in `results/permutation-1000/`:

- `scanone.csv`: observed LOD scores.
- `permutations.csv`: 1,000 permutation maxima.
- `thresholds.csv`: LOD thresholds for alpha 0.37, 0.05, and 0.01.
- `qtl-scan.png`: scan with labeled threshold lines.

This single-phenotype `scanone` run does not demonstrate a performance
bottleneck. Two-dimensional `scantwo` scans and the full phenotype loop
remain untested and may have different costs. The unfinished `rqtl2`/VCF
analysis is also unvalidated. Measure the selected workload before
choosing a student optimization target.
