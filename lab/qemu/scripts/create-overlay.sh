#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
source "$SCRIPT_DIR/common.sh"
require_file "$BASE_IMAGE"
mkdir -p "$RUNTIME_DIR"
[[ ! -e "$OVERLAY" ]] || die "overlay already exists: $OVERLAY; run reset.sh first"
qemu-img create -f qcow2 -F qcow2 -b "$BASE_IMAGE" "$OVERLAY" >/dev/null
info "created disposable overlay: $OVERLAY"
