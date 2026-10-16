#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
source "$SCRIPT_DIR/common.sh"
"$SCRIPT_DIR/shutdown.sh"
runtime_path_is_safe "$RUNTIME_DIR" || die "refusing to remove unsafe runtime path: $RUNTIME_DIR"
[[ "$RUNTIME_DIR" == "$REPO_ROOT/.lab/qemu" || "$RUNTIME_DIR" == "$REPO_ROOT/.lab/qemu/"* ]] || die "runtime directory must remain below repository .lab/qemu"
rm -rf -- "$RUNTIME_DIR"
mkdir -p "$RUNTIME_DIR"
info "removed disposable runtime files; base-image cache was preserved"
