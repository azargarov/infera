#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

cleanup() {
  ./lab/qemu/scripts/shutdown.sh >/dev/null 2>&1 || true
  ./lab/qemu/scripts/reset.sh >/dev/null 2>&1 || true
}
trap cleanup EXIT

./lab/qemu/scripts/check-prereqs.sh
./lab/qemu/scripts/fetch-base-image.sh

baseline() {
  ./lab/qemu/scripts/reset.sh
  ./lab/qemu/scripts/create-overlay.sh
  ./lab/qemu/scripts/create-seed.sh
  ./lab/qemu/scripts/boot.sh
  ./lab/qemu/scripts/wait-for-ssh.sh
  ./lab/qemu/scripts/verify-baseline.sh
}

baseline
echo 'QEMU healthy baseline passed'

for scenario in service-failure-001 ambiguous-001 resource-pressure-001 storage-001 network-dependency-001; do
  baseline
  "./lab/scenarios/$scenario/inject.sh" "$scenario"
  "./lab/scenarios/$scenario/verify.sh" "$scenario"
  echo "QEMU scenario setup passed: $scenario"
done

baseline
pm_run="pm-restart-001-$(date -u +%Y%m%dT%H%M%SZ)"
./lab/scenarios/pm-restart-001/prepare-run.sh "$pm_run"
test ! -e "runs/$pm_run/actions/approval.yaml"
echo 'QEMU PM preparation passed; no approval or restart was performed'

echo 'QEMU integration checks passed; no LLM execution was performed'
