# GBCF nf-core Pipelines

- Domain: next-generation sequencing analysis on CRC.
- Contact: Bharat Mishra (`bmishra2@nd.edu`).
- Workflow: [`nf-core/rnaseq`](https://github.com/nf-core/rnaseq) 3.26.0
  (commit `e7ca462`), pinned as the `code/` submodule. Bharat suggested it as a more
  complex, memory-intensive workflow than the smaller GBCF examples; the
  `scRNA_Seq_explorer` alternative he shared is not being pursued.
- Course fit: workflow-level performance, scheduling, data movement, resource
  tuning, and scaling.

## Current status

The pipeline runs end to end on CRC with its built-in `test` profile under
both Grid Engine and HTCondor, using Nextflow 26.04.6 and Apptainer.
The test data is only a smoke test. A representative dataset, its reference
genome, and a specific performance question still need to come from Bharat.

## Test input

The `test` profile downloads about 25 MB from `nf-core/test-datasets`:

- 7 sequencing runs in 11 `fastq.gz` files (4 paired-end, 3 single-end), each
  run 50,000 reads of 101 bp, merged into 5 samples.
- A small yeast genome excerpt (229 KB) with a GTF of 125 genes, a
  transcriptome, and a prebuilt Salmon index.
- Small BBSplit contamination references.

A real RNA-seq sample is typically 20–50 million read pairs against a
multi-gigabyte genome, so none of the timings below reflect production cost.

## Setup: prefetch containers

Compute nodes cannot build Apptainer images from OCI layers (`proot error:
ptrace(TRACEME): Operation not permitted`), so pull them on a front end first:

```bash
scripts/prefetch-containers.sh
```

This fills `.apptainer/` with the 27 images listed in
`scripts/containers-test.txt` (about 16 GB). `run-test.sh` runs the same
script with `--check` and stops if any image is missing.

## Run with Grid Engine (recommended)

Submit from `crcfe01.crc.nd.edu` or `crcfe02.crc.nd.edu`:

```bash
cd projects/gbcf-nf-core-rnaseq
qsub scripts/rnaseq-test.sge
```

The job requests 8 slots in the `long` queue and writes to
`results/test-run-sge/`, logging to `results/test-run-sge.uge.log`.
Grid Engine rejects jobs without a Kerberos ticket ("job does not provide an
AFS token"); an ordinary login shell has one.

## Run with HTCondor

Submit from `condorfe.crc.nd.edu`:

```bash
cd projects/gbcf-nf-core-rnaseq
condor_submit scripts/rnaseq-test.submit
```

The job writes to `results/test-run/`. CRC's HTCondor slots can be
preempted at any time. After an eviction the job restarts, and `run-test.sh`
resumes the existing Nextflow session instead of starting over.

## Validation results

| Run | Host | Tasks | Wall time |
| --- | --- | --- | --- |
| Grid Engine, from scratch | `d12chas325`, 8 slots | 234 completed | 7m 44s |
| HTCondor, evicted once | `qa-l40s-007`, then `d32cepyc037` | 164 completed + 70 resumed | 5m 11s + 4m 22s |

From the Grid Engine trace (`results/trace.txt`), task run times sum to 795 s
and the largest peak RSS is 4.1 GB (`PICARD_MARKDUPLICATES`).
The largest contributors are:

| Process | Tasks | Total run time | Peak RSS |
| --- | --- | --- | --- |
| `STAR_ALIGN` | 5 | 315 s | 951 MB |
| `BBMAP_BBSPLIT` | 6 | 115 s | 1.4 GB |
| `MULTIQC` | 1 | 51 s | 1.1 GB |
| `PICARD_MARKDUPLICATES` | 5 | 30 s | 4.1 GB |

Both runs produced BAM files, bigWigs, QC reports, and merged gene count
tables for 5 samples and 125 genes. The MultiQC report is at
`results/multiqc/star_salmon/multiqc_report.html`. Salmon-only counts are
identical between the runs; STAR + Salmon counts and TPMs differ by at most
0.09% relative, consistent with multithreaded alignment and quantification.

## Files

- `scripts/prefetch-containers.sh`: pull or check container images.
- `scripts/containers-test.txt`: images used by the `test` profile.
- `scripts/run-test.sh`: shared launcher; optional run directory argument,
  `RESUME=1` to force resume.
- `scripts/rnaseq-test.sge`, `scripts/rnaseq-test.submit`: batch jobs.
- `scripts/nextflow.config`: lets reports overwrite on reruns.

## Project packet

Still needed from the owner: a representative dataset (or its CRC path) and
reference genome, the matching pipeline parameters, expected results,
data-access constraints, and a bounded performance question. Measure the
baseline on that input before choosing a student optimization target.
