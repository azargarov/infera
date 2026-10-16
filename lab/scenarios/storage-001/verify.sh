#!/usr/bin/env bash
set -euo pipefail
SCENARIO_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCENARIO_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
SCENARIO_ID=${1:-}
[[ "$SCENARIO_ID" == storage-001 ]] || die "usage: $0 storage-001"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
check() { lab_ssh "$@" >/dev/null || die "injection check failed: $*"; }
check 'test "$(hostname)" = infera-lab'
check 'test "$(findmnt -n -o TARGET /srv/infera-data)" = /srv/infera-data'
check 'test "$(findmnt -n -o FSTYPE /srv/infera-data)" = ext4'
check "df -P /srv/infera-data | awk 'NR == 2 {gsub(\"%\", \"\", \$5); exit ! (\$5 + 0 >= 95)}'"
check "df -P / | awk 'NR == 2 {gsub(\"%\", \"\", \$5); exit ! (\$5 + 0 < 90)}'"
check 'test "$(systemctl is-active demo-api.service)" = active'
check 'test "$(curl -sS -o /tmp/infera-storage-check.out -w "%{http_code}" http://127.0.0.1:18080/storage-write)" = 507'
check "journalctl -u demo-api.service --no-pager -n 100 | grep -q 'storage_write_failure errno=28 path=/srv/infera-data'"
check 'test "$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/health)" = 200'
info "storage-001 injection verification passed"
