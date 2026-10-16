#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
source "$SCRIPT_DIR/common.sh"
require_file "$SSH_KEY"
[[ -f "$PID_FILE" ]] || die "QEMU is not running; run boot.sh first"
for attempt in $(seq 1 60); do
  if lab_ssh true >/dev/null 2>&1; then info "SSH is ready on $SSH_HOST:$SSH_PORT"; exit 0; fi
  sleep 2
done
die "SSH did not become ready; inspect $SERIAL_LOG"
