#!/usr/bin/env bash
# Pull the Apptainer images used by the nf-core/rnaseq test profile into the
# shared cache that run-test.sh points Nextflow at.
#
# Run this on a CRC front end (for example condorfe.crc.nd.edu), not inside an
# HTCondor job: building a SIF from OCI layers fails on compute nodes with
# "proot error: ptrace(TRACEME): Operation not permitted".
#
# With --check, only report missing images and exit nonzero if any are missing.

set -euo pipefail

project_dir=$(cd "$(dirname "$0")/.." && pwd)
cache="$project_dir/.apptainer"
list="$project_dir/scripts/containers-test.txt"

check_only=0
[ "${1:-}" = "--check" ] && check_only=1

mkdir -p "$cache"
missing=0

while read -r ref; do
    [ -z "$ref" ] && continue

    # Reproduce Nextflow's cache file name: drop the URL scheme, prefix
    # registry-less names with quay.io (nf-core's apptainer registry), and
    # replace '/' and ':' with '-'.
    case "$ref" in
        *://*)
            name=${ref#*://}
            src=$ref
            ;;
        *)
            first=${ref%%/*}
            case "$first" in
                *.*) name=$ref ;;
                *) name="quay.io/$ref" ;;
            esac
            src="docker://$name"
            ;;
    esac
    img="$cache/$(printf '%s' "$name" | tr '/:' '--').img"

    if [ -s "$img" ]; then
        echo "cached   $ref"
        continue
    fi

    if [ "$check_only" -eq 1 ]; then
        echo "MISSING  $ref"
        missing=$((missing + 1))
        continue
    fi

    echo "pulling  $ref"
    rm -f "$img.part"
    apptainer pull "$img.part" "$src"
    mv "$img.part" "$img"
done < "$list"

if [ "$missing" -gt 0 ]; then
    echo "$missing image(s) missing; run $0 on a front end first." >&2
    exit 1
fi
