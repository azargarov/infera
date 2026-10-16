#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
source "$SCRIPT_DIR/common.sh"
require_file "$OVERLAY"
require_file "$SEED_IMAGE"
[[ ! -f "$PID_FILE" ]] || die "QEMU PID file exists: $PID_FILE; use shutdown.sh or reset.sh"
mkdir -p "$RUNTIME_DIR"
qemu-system-x86_64 -name infera-lab -machine type=q35,accel=kvm -cpu host -m "$VM_MEMORY" -smp "$VM_VCPUS" -drive "file=$OVERLAY,if=virtio,format=qcow2" -drive "file=$SEED_IMAGE,media=cdrom,readonly=on" -nic "user,model=virtio,hostfwd=tcp:$SSH_HOST:$SSH_PORT-:22" -display none -serial "file:$SERIAL_LOG" -daemonize -pidfile "$PID_FILE"
info "booted infera-lab; serial log: $SERIAL_LOG"
