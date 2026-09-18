#!/usr/bin/env bash
# Reassemble the owner-provided VCF, split only to satisfy GitHub's file limit.
set -euo pipefail

project_dir=$(cd "$(dirname "$0")/.." && pwd)
data_dir="$project_dir/data"
archive="$data_dir/hb3_dd2.gatk.final.vcf.gz"
output="$data_dir/hb3_dd2.gatk.final.vcf"

cat "$data_dir"/hb3_dd2.gatk.final.vcf.gz.part-* > "$archive"
echo "deb84c98cae97f43486b71aae1caf5b2b5a7f29bd1fbb3adadf55007c0ca08cc  $archive" | sha256sum -c -
gzip -dc "$archive" > "$output"
echo "2c8e7ad82beb998369c5ec79867811eac9f28bc5e76574e03407665f896622a3  $output" | sha256sum -c -
echo "$output"
