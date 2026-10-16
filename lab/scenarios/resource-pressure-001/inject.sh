#!/usr/bin/env bash
set -euo pipefail
SCENARIO_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCENARIO_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
SCENARIO_ID=${1:-}
[[ "$SCENARIO_ID" == resource-pressure-001 ]] || die "usage: $0 resource-pressure-001"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
require_file "$PID_FILE"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
lab_ssh 'test "$(hostname)" = infera-lab' || die "target is not infera-lab"
lab_ssh 'test "$(systemctl is-active demo-api.service)" = active' || die "demo-api.service is not healthy before injection"
lab_ssh 'curl -fsS http://127.0.0.1:18080/health | grep -q "OK demo-api"' || die "API baseline health failed"
"$SCENARIO_DIR/measure.sh" baseline
lab_ssh 'sudo install -d -m 0755 /var/lib/infera && sudo touch /var/lib/infera/resource-pressure-active && sudo systemctl start infera-pressure-worker@1.service infera-pressure-worker@2.service'
sleep 3
"$SCENARIO_DIR/measure.sh" pressure
mkdir -p "$RUNTIME_DIR"
cat > "$RUNTIME_DIR/injection-resource-pressure-001.yaml" <<RECORD
scenario_id: resource-pressure-001
mutation: started two bounded synthetic CPU workers and enabled bounded API work
pressure_threshold: worker CPU total above 100 percent
baseline_reference: resource-pressure-baseline.yaml
pressure_reference: resource-pressure-pressure.yaml
target: infera-lab
ssh_endpoint: 127.0.0.1:2222
reversible_by: disposable overlay reset
RECORD
info "injected resource-pressure-001 into infera-lab"
