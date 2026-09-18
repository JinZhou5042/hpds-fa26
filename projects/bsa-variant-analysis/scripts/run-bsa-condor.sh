#!/usr/bin/env bash
# Re-run the BSA baseline via HTCondor, submitted from condorfe.
set -euo pipefail

export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"
source /software/Modules/5.6.1/init/bash
module load R/4.4.0/gcc/11.5.0
export R_LIBS_USER="$PWD/.R-library"
export OMP_NUM_THREADS=1

mkdir -p results/baseline-recheck

echo "host=$(hostname) start=$(date -Is)"
echo "source_revision=$(git -C code/upstream rev-parse HEAD)"
sha256sum data/BSA6.1.multi.MAL31xKH004.SNP.filter.table
/usr/bin/time -v Rscript scripts/run-bsa.R \
      data/BSA6.1.multi.MAL31xKH004.SNP.filter.table \
      code/upstream/BSA_OPTIMISATION_MAL_KH results/baseline-recheck
(cd results/baseline-recheck && sha256sum *.csv > SHA256SUMS)
echo "end=$(date -Is)"
