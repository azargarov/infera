#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
SCENARIO_ID=${1:-}
[[ "$SCENARIO_ID" == ambiguous-001 ]] || die "usage: $0 ambiguous-001"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
require_file "$PID_FILE"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
lab_ssh 'test "$(hostname)" = infera-lab' || die "target is not infera-lab"
lab_ssh 'test "$(systemctl is-active demo-db.service)" = active' || die "demo-db.service is not healthy before injection"
lab_ssh "python3 -c 'import socket; s=socket.create_connection((\"127.0.0.1\",15432),2); s.sendall(b\"health\\n\"); assert s.recv(64).startswith(b\"OK demo-db\")'" || die "database health check failed before injection"
lab_ssh 'sudo install -d -m 0755 /var/lib/infera && sudo touch /var/lib/infera/ambiguous-api-state && sudo systemctl restart demo-api.service'
lab_ssh 'curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/health | grep -q 503' || die "demo-api did not enter generic degraded state"
mkdir -p "$RUNTIME_DIR"
cat > "$RUNTIME_DIR/injection-ambiguous-001.yaml" <<RECORD
scenario_id: ambiguous-001
mutation: enabled synthetic generic degraded API state
visible_dependency_state: demo-db.service remains healthy
missing_decisive_source: recent API failure detail is not emitted by the generic degraded state
target: infera-lab
ssh_endpoint: 127.0.0.1:2222
reversible_by: disposable overlay reset
RECORD
info "injected ambiguous-001 into infera-lab"
