#!/usr/bin/env bash
set -euo pipefail
SCENARIO_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCENARIO_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
SCENARIO_ID=${1:-}
[[ "$SCENARIO_ID" == storage-001 ]] || die "usage: $0 storage-001"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
require_file "$PID_FILE"
"$REPO_ROOT/lab/qemu/scripts/wait-for-ssh.sh" >/dev/null
lab_ssh 'test "$(hostname)" = infera-lab' || die "target is not infera-lab"
lab_ssh 'test "$(findmnt -n -o TARGET /srv/infera-data)" = /srv/infera-data' || die "synthetic storage mount is not present"
lab_ssh 'test "$(systemctl is-active demo-api.service)" = active' || die "demo-api.service is not healthy before injection"
lab_ssh 'test "$(curl -sS -o /tmp/infera-storage-baseline.out -w "%{http_code}" http://127.0.0.1:18080/storage-write)" = 200' || die "synthetic application write did not succeed before injection"
mkdir -p "$RUNTIME_DIR"
cat > "$RUNTIME_DIR/storage-baseline.yaml" <<BASELINE
scenario_id: storage-001
target: infera-lab
operation: synthetic application write
status: succeeded
http_status: 200
scope: synthetic storage mount
reversible_by: disposable overlay reset
BASELINE
lab_ssh "sudo -u infera sh -c 'dd if=/dev/zero of=/srv/infera-data/fill.bin bs=4096 status=none' >/tmp/infera-storage-fill.log 2>&1 || true"
lab_ssh 'test "$(curl -sS -o /tmp/infera-storage-failure.out -w "%{http_code}" http://127.0.0.1:18080/storage-write)" = 507' || die "synthetic application write did not fail after injection"
cat > "$RUNTIME_DIR/injection-storage-001.yaml" <<RECORD
scenario_id: storage-001
mutation: filled the disposable synthetic storage filesystem
application_probe: demo-api storage-write returned 507
target: infera-lab
ssh_endpoint: 127.0.0.1:2222
reversible_by: disposable overlay reset
RECORD
info "injected storage-001 into infera-lab"
