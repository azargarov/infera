#!/usr/bin/env bash
set -euo pipefail
SCENARIO_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCENARIO_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
SCENARIO_ID=${1:-}
[[ "$SCENARIO_ID" == network-dependency-001 ]] || die "usage: $0 network-dependency-001"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
check() { lab_ssh "$@" >/dev/null || die "injection check failed: $*"; }
check 'test "$(hostname)" = infera-lab'
check 'test "$(systemctl is-active demo-upstream.service || true)" != active'
check 'getent hosts demo-upstream.local | awk '\''$1 == "127.0.0.1"'\'' | grep -q .'
check '! ss -ltn | grep -q ":19090 "'
check 'ip route | grep -q default'
check 'test "$(systemctl is-active demo-api.service)" = active'
check 'test "$(curl -sS -o /tmp/infera-network-check.out -w "%{http_code}" http://127.0.0.1:18080/health)" = 503'
check "journalctl -u demo-api.service --no-pager -n 100 | grep -q 'network_dependency_connection_failure endpoint=demo-upstream.local:19090'"
check 'test "$(hostname)" = infera-lab'
info "network-dependency-001 injection verification passed"
