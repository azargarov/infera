#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
SCENARIO_ID=${1:-}
[[ "$SCENARIO_ID" == service-failure-001 ]] || die "usage: $0 service-failure-001"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
check() { lab_ssh "$@" >/dev/null || die "injection check failed: $*"; }
check 'test "$(hostname)" = infera-lab'
check 'test "$(systemctl is-active demo-db.service || true)" != active'
check 'test "$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/health)" = 503'
check "journalctl -u demo-api.service --no-pager -n 100 | grep -q 'dependency_connection_failure'"
check "journalctl -t demo-api --no-pager -n 100 | grep -q 'synthetic unrelated warning'"
check 'test -f /var/lib/infera/service-failure-001-injected'
check 'true'
info "service-failure-001 injection verification passed"
