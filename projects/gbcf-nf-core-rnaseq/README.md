# GBCF nf-core RNA-seq

[nf-core/rnaseq](https://github.com/nf-core/rnaseq) is a widely used
Nextflow pipeline that takes raw RNA-seq reads through alignment,
quantification, and QC, running dozens of containerized tools per sample.
The question here is how to run it well on CRC: scheduling, resource use,
data movement, and scaling.

- Contact: Bharat Mishra (`bmishra2@nd.edu`)
- Code: nf-core/rnaseq 3.26.0, pinned as the `code/` submodule
- Data: the pipeline's built-in `test` profile, about 25 MB downloaded at run
  time (a yeast genome excerpt and 5 small samples). Real samples are tens of
  millions of reads against a multi-gigabyte genome. Bharat has larger real
  datasets and will share one on the CRC shared file system.

## Setup

Compute nodes can't build Apptainer images, so pull the containers on a front
end first (27 images, about 16 GB, into `.apptainer/`):

```bash
scripts/prefetch-containers.sh
```

## Minimal run

From this directory, with Grid Engine on `crcfe01` or `crcfe02`:

```bash
mkdir -p results
qsub scripts/rnaseq-test.sge
```

Or with HTCondor on `condorfe`:

```bash
mkdir -p results
condor_submit scripts/rnaseq-test.submit
```

Both call `scripts/run-test.sh` and write to `results/`. HTCondor jobs can be
evicted at any time. When that happens the job restarts and Nextflow resumes
where it left off.
