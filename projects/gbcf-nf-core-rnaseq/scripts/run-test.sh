#!/usr/bin/env bash
# Run the nf-core/rnaseq test profile with Apptainer.
#
# Usage: run-test.sh [run_dir]      (default: results/test-run)
#
# Each run gets its own work, results, and report files under run_dir.
# Set RESUME=1 to reuse run_dir's Nextflow cache instead of starting over.
# Container images must already be in the cache; see prefetch-containers.sh.

set -euo pipefail

project_dir=$(cd "$(dirname "$0")/.." && pwd)
run_dir=${1:-$project_dir/results/test-run}

export JAVA_CMD=/software/j/java/jdk-26.0.1/bin/java
export PATH="$(dirname "$JAVA_CMD"):/usr/bin:/bin"
export PROOT_NO_SECCOMP=1
export NXF_HOME="$project_dir/.nextflow"
export NXF_APPTAINER_CACHEDIR="$project_dir/.apptainer"
export NXF_LOCAL_CPUS=8
export NXF_LOCAL_MEMORY=24GB

"$project_dir/scripts/prefetch-containers.sh" --check

mkdir -p "$NXF_HOME" "$run_dir"
cd "$run_dir"

# HTCondor reruns this script from the start when a job is evicted, so resume
# automatically if run_dir already holds a Nextflow session.
resume=()
if [ "${RESUME:-0}" = 1 ] || [ -s "$run_dir/.nextflow/history" ]; then
    echo "Resuming the Nextflow session in $run_dir"
    resume=(-resume)
fi

exec "$project_dir/scripts/nextflow" run "$project_dir/code" \
    -profile test,apptainer \
    -c "$project_dir/scripts/nextflow.config" \
    -work-dir "$run_dir/work" \
    --outdir "$run_dir/results" \
    -with-report "$run_dir/report.html" \
    -with-timeline "$run_dir/timeline.html" \
    -with-trace "$run_dir/trace.txt" \
    -ansi-log false \
    "${resume[@]}"
