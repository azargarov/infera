#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
SCENARIO_ID=${1:-}
[[ "$SCENARIO_ID" == service-failure-001 ]] || die "usage: $0 service-failure-001"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
require_file "$PID_FILE"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
lab_ssh 'test "$(hostname)" = infera-lab' || die "target is not infera-lab"
lab_ssh 'test "$(systemctl is-active demo-db.service)" = active' || die "demo-db.service is not healthy before injection"
lab_ssh 'sudo systemctl stop demo-db.service'
lab_ssh 'sudo logger -p user.warning -t demo-api "synthetic unrelated warning: cache metadata refresh deferred"'
lab_ssh 'sudo install -d -m 0755 /var/lib/infera && printf "%s\n" "service-failure-001: demo-db stopped; unrelated warning recorded" | sudo tee /var/lib/infera/service-failure-001-injected >/dev/null'
lab_ssh 'curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/health | grep -q 503' || die "demo-api did not become degraded"
mkdir -p "$RUNTIME_DIR"
cat > "$RUNTIME_DIR/injection-service-failure-001.yaml" <<RECORD
scenario_id: service-failure-001
mutation: stopped demo-db.service
warning: recorded synthetic unrelated warning in demo-api journal
target: infera-lab
ssh_endpoint: 127.0.0.1:2222
reversible_by: disposable overlay reset
RECORD
info "injected service-failure-001 into infera-lab"
