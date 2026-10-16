#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
SCENARIO_ID=${1:-}
[[ "$SCENARIO_ID" == resource-pressure-001 ]] || die "usage: $0 resource-pressure-001"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
check() { lab_ssh "$@" >/dev/null || die "resource-pressure injection check failed: $*"; }
check 'test "$(hostname)" = infera-lab'
check 'test "$(systemctl is-active infera-pressure-worker@1.service)" = active && test "$(systemctl is-active infera-pressure-worker@2.service)" = active'
check "ps -eo pcpu=,args= | awk '/infera-pressure-worker.py/ {sum+=\$1; count++} END {exit !(count >= 2 && sum > 100)}'"
check 'test "$(systemctl is-active demo-api.service)" = active'
check 'curl -fsS http://127.0.0.1:18080/health | grep -q "OK demo-api"'
check 'true'
base=$(awk '$1 == "median_seconds:" {print $2}' "$RUNTIME_DIR/resource-pressure-baseline.yaml")
pressure=$(awk '$1 == "median_seconds:" {print $2}' "$RUNTIME_DIR/resource-pressure-pressure.yaml")
[[ "$base" =~ ^[0-9]+\.[0-9]+$ && "$pressure" =~ ^[0-9]+\.[0-9]+$ ]] || die "latency references are invalid"
awk -v base="$base" -v pressure="$pressure" 'BEGIN {exit !(pressure > base + 0.05)}' || die "API latency did not exceed the bounded degradation threshold"
info "resource-pressure-001 injection verification passed; baseline=${base}s pressure=${pressure}s"
