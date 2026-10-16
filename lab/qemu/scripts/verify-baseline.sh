#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
source "$SCRIPT_DIR/common.sh"
"$SCRIPT_DIR/wait-for-ssh.sh" >/dev/null
check() { lab_ssh "$@" >/dev/null || die "baseline check failed: $*"; }
check 'test "$(hostname)" = infera-lab'
check "grep -q '^ID=ubuntu$' /etc/os-release && grep -q '^VERSION_ID=\\\"24.04\\\"$' /etc/os-release"
check "cloud-init status --wait 2>/dev/null | grep -q 'status: done'"
check 'test "$(systemctl is-active demo-db.service)" = active'
check 'test "$(systemctl is-active demo-upstream.service)" = active'
check 'test "$(systemctl is-active demo-api.service)" = active'
check "ss -ltn | grep -q ':15432 '"
check "ss -ltn | grep -q ':19090 '"
check "ss -ltn | grep -q ':18080 '"
check "python3 -c 'import socket; s=socket.create_connection((\"127.0.0.1\",15432),2); s.sendall(b\"health\\n\"); assert s.recv(64).startswith(b\"OK demo-db\")'"
check "python3 -c 'import socket; s=socket.create_connection((\"demo-upstream.local\",19090),2); s.sendall(b\"health\\n\"); assert s.recv(64).startswith(b\"OK demo-upstream\")'"
check "python3 -c 'from urllib.request import urlopen; assert urlopen(\"http://127.0.0.1:18080/health\",timeout=2).read().startswith(b\"OK demo-api\")'"
check "test \"\$(df -P / | awk 'NR==2 {print 100-\$5}')\" -gt 10"
info "synthetic Linux baseline verification passed"
