#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
source "$SCRIPT_DIR/common.sh"
if [[ ! -f "$PID_FILE" ]]; then info "QEMU is not running"; exit 0; fi
pid=$(cat "$PID_FILE" 2>/dev/null || true)
if [[ ! "$pid" =~ ^[0-9]+$ ]] || ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$PID_FILE"
  info "QEMU is not running"
  exit 0
fi
lab_ssh "sudo poweroff" >/dev/null 2>&1 || true
for _ in $(seq 1 30); do
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$PID_FILE"
    info "guest stopped"
    exit 0
  fi
  sleep 1
done
kill "$pid" 2>/dev/null || true
rm -f "$PID_FILE"
info "stopped QEMU process after graceful shutdown timeout"
