# QTL Workflow

- Domain: genetic linkage mapping and variant interpretation.
- Contact: Tarrick Qahash (`tqahash@nd.edu`).
- Technical profile: R-based multiple-QTL modeling and/or a workflow that
  finds QTL peaks, searches genes in LOD intervals, and examines mutations
  using VCF and reference-genome data.
- Course fit: modernize an older MQM workflow to `rqtl2`, or parallelize the
  repeated VCF/gene-interval processing.

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

Package installation is only needed once. The run was verified on 2026-09-07
on `condorfe.crc.nd.edu` with R 4.4.0 and qtl 1.74. It uses the supplied
CSV and the original script's second phenotype (`CQ..IC50.`), Haley-Knott
scan, and batch size, with a fixed seed and only 10 permutations.
It reads 37 individuals, 625 markers, and 14 chromosomes and writes
`results/scanone.csv`, `results/permutations.csv`, and
`results/qtl-scan.png`. The peak was marker M202 on chromosome 7,
position 21.807, LOD 9.66499. The measured analysis and output time was
0.356 seconds, excluding package installation and R startup.

The original import treats `N/A` genotype entries as missing. One individual
has no value for this phenotype and is excluded from the scan. Markers on
chromosome 13 include duplicate positions. These warnings are retained in
the log; the supplied data and original `code/QTL_Code.R` are unchanged.

The minimal run verifies basic execution and finite scan/permutation output.
Tarrick confirmed on 2026-09-07 that the observed chromosome 7 peak is
expected for chloroquine. This is an owner confirmation, not a numerical
comparison against a supplied reference file. Ten permutations are only a
smoke test; use the run below for the original permutation count.

## Single-phenotype permutation run

After the environment setup above, run:

```bash
Rscript scripts/permutation-run.R > results/permutation-1000.log 2>&1
```

Verified on 2026-09-07 with the same host, R version, package, input,
phenotype, and scan parameters as the minimal run. The seed is 20260907.
All 1,000 permutation values were finite; the 625-marker scan output
matched the minimal run exactly. Outputs are in `results/permutation-1000/`:

- `scanone.csv`: observed LOD scores.
- `permutations.csv`: 1,000 permutation maxima.
- `thresholds.csv`: LOD thresholds for alpha 0.37, 0.05, and 0.01.
- `qtl-scan.png`: scan with labeled threshold lines.

The permutation call took 0.684 seconds; analysis and output together took
0.912 seconds, excluding R startup and package installation. These are
single-run timings on the CRC front end, not compute-node benchmarks.
The peak remains M202 on chromosome 7 (LOD 9.66499), above all three
thresholds. The input warnings described above remain unchanged.

This single-phenotype `scanone` run does not demonstrate a performance
bottleneck. Two-dimensional `scantwo` scans and the full phenotype loop
remain untested and may have different costs. The unfinished `rqtl2`/VCF
analysis is also unvalidated. Measure the selected workload before
choosing a student optimization target.

Observed thresholds for this seed:

| Alpha | LOD threshold |
| --- | --- |
| 37% | 2.187616 |
| 5% | 3.282060 |
| 1% | 4.310687 |
