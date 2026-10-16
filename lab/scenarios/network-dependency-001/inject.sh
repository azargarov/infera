#!/usr/bin/env bash
set -euo pipefail
SCENARIO_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCENARIO_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
SCENARIO_ID=${1:-}
[[ "$SCENARIO_ID" == network-dependency-001 ]] || die "usage: $0 network-dependency-001"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
require_file "$PID_FILE"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
lab_ssh 'test "$(hostname)" = infera-lab' || die "target is not infera-lab"
lab_ssh 'test "$(systemctl is-active demo-upstream.service)" = active' || die "demo-upstream.service is not healthy before injection"
lab_ssh "getent hosts demo-upstream.local | awk '\$1 == \"127.0.0.1\"' | grep -q ." || die "synthetic dependency name does not resolve locally"
lab_ssh 'test "$(systemctl is-active demo-api.service)" = active' || die "demo-api.service is not healthy before injection"
lab_ssh 'sudo install -d -m 0755 /var/lib/infera && sudo touch /var/lib/infera/network-dependency-active && sudo systemctl stop demo-upstream.service'
lab_ssh 'test "$(curl -sS -o /tmp/infera-network-failure.out -w "%{http_code}" http://127.0.0.1:18080/health)" = 503' || die "demo-api did not report dependency failure"
mkdir -p "$RUNTIME_DIR"
cat > "$RUNTIME_DIR/injection-network-dependency-001.yaml" <<RECORD
scenario_id: network-dependency-001
mutation: stopped the disposable synthetic dependency listener
name_resolution: preserved for the synthetic dependency name
target: infera-lab
ssh_endpoint: 127.0.0.1:2222
reversible_by: disposable overlay reset
RECORD
info "injected network-dependency-001 into infera-lab"
