#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
PHASE=${1:-}
[[ "$PHASE" == baseline || "$PHASE" == pressure ]] || die "usage: $0 baseline|pressure"
require_file "$PID_FILE"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
samples=()
for _ in 1 2 3 4 5; do
  samples+=("$(lab_ssh 'curl -sS -o /dev/null -w "%{time_total}" http://127.0.0.1:18080/health')")
done
median=$(printf '%s\n' "${samples[@]}" | sort -n | awk 'NR==3 {print}')
[[ "$median" =~ ^[0-9]+\.[0-9]+$ ]] || die "latency measurement was not numeric"
mkdir -p "$RUNTIME_DIR"
{
  echo "phase: $PHASE"
  echo "target: infera-lab"
  echo "sample_seconds:"
  printf '  - %s\n' "${samples[@]}"
  echo "median_seconds: $median"
} > "$RUNTIME_DIR/resource-pressure-$PHASE.yaml"
info "$PHASE API latency median: ${median}s"
