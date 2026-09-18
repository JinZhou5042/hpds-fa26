# QTL Workflow

QTL mapping of drug response in a *Plasmodium falciparum* genetic cross
(Dd2 × HB3), followed by a search for genes and mutations inside the QTL
intervals using the cross's VCF. Written in R with the `qtl` package.

- Contact: Tarrick Qahash (`tqahash@nd.edu`)
- Code: `code/QTL_Code.R`
- Data: `data/*.csv` (linkage map and phenotypes) and the full VCF, split
  into two parts to fit GitHub's file limit. Rebuild it with
  `scripts/restore-vcf.sh`.

## Minimal run

From this directory on CRC:

```bash
module load R/4.4.0/gcc/11.5.0
mkdir -p .R-library results
Rscript -e 'install.packages("qtl", lib=".R-library", repos="https://cloud.r-project.org")'
Rscript scripts/minimal-run.R > results/minimal-run.log 2>&1
```

`minimal-run.R` does one single-trait scan from the original script (the
`CQ..IC50.` phenotype) with only 10 permutations. `scripts/permutation-run.R`
runs the same scan with the original 1,000. Neither covers the
two-dimensional scans, the loop over all phenotypes, or the VCF part of
`QTL_Code.R`.

The input produces warnings about missing genotypes and duplicate marker
positions on chromosome 13. They are expected.
