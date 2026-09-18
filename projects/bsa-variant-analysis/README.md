# BSA and Variant Analysis

Bulk segregant analysis (BSA) of a *Plasmodium falciparum* genetic cross
(MAL31 × KH004). The R workflow computes reference-allele frequencies for
each bulk sample from read depths, drops low-depth sites, removes local
outliers with a sliding-window MAD filter, and smooths the frequencies along
each chromosome.

- Contact: Nirjhar Bhattacharyya (`nbhattac@nd.edu`)
- Code: <https://github.com/NirjharBhattacharyya/Bulk_Segregation_Analysis_Ferdig_Lab>.
  The repository is private, ask Nirjhar for access. The analysis is in
  `BSA_OPTIMISATION_MAL_KH`.
- Data: `data/BSA6.1.multi.MAL31xKH004.SNP.filter.table` (26.7 MB), a
  tab-separated SNP table with 12,803 variants on 14 chromosomes and allele
  and read depths for 114 bulk samples.

## Minimal run

Clone the code into `code/upstream` (see `code/README.md`). Then, once, from
this directory on a CRC front end:

```bash
module load R/4.4.0/gcc/11.5.0
mkdir -p .R-library results
export R_LIBS_USER=$PWD/.R-library
Rscript -e 'install.packages(c("dplyr","magrittr","locfit","reshape2","ggplot2"), lib=".R-library", repos="https://cloud.r-project.org")'
# The current Deriv (needed by doBy) requires R 4.5, so install an older one.
Rscript -e 'install.packages("https://cloud.r-project.org/src/contrib/Archive/Deriv/Deriv_4.1.6.tar.gz", lib=".R-library", repos=NULL, type="source")'
Rscript -e 'install.packages("doBy", lib=".R-library", repos="https://cloud.r-project.org")'
```

Submit from `crcfe01` or `crcfe02`:

```bash
qsub scripts/run-bsa.sge
```

`BSA_OPTIMISATION_MAL_KH` is a saved interactive R session and can't be run
as is. `scripts/run-bsa.R` runs its functions with the original parameters as
a batch job, writing to `results/baseline/`. It stops before the QTLseqr G′
section, which needs a package and inputs that aren't included. For HTCondor,
use `scripts/run-bsa-condor.submit` instead.
