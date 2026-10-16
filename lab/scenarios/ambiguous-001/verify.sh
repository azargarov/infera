#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
SCENARIO_ID=${1:-}
[[ "$SCENARIO_ID" == ambiguous-001 ]] || die "usage: $0 ambiguous-001"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
check() { lab_ssh "$@" >/dev/null || die "ambiguous injection check failed: $*"; }
check 'test "$(hostname)" = infera-lab'
check 'test "$(systemctl is-active demo-db.service)" = active'
check 'python3 -c '\''import socket; s=socket.create_connection(("127.0.0.1",15432),2); s.sendall(b"health\n"); assert s.recv(64).startswith(b"OK demo-db")'\'''
check 'test "$(systemctl is-active demo-api.service)" = active'
check 'test "$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/health)" = 503'
check 'curl -sS http://127.0.0.1:18080/health | grep -q diagnostic-evidence-incomplete'
check "! journalctl -u demo-api.service --no-pager -n 100 | grep -Eq 'dependency_connection_failure|connection refused|configuration error|Traceback'"
check 'test -f /var/lib/infera/ambiguous-api-state'
check 'true'
info "ambiguous-001 injection verification passed"
