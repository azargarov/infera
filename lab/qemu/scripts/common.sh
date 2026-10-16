#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
LAB_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
REPO_ROOT=$(cd -- "$LAB_DIR/../.." && pwd)
RUNTIME_DIR=${INFERA_LAB_RUNTIME_DIR:-"$REPO_ROOT/.lab/qemu"}
CACHE_DIR=${INFERA_LAB_CACHE_DIR:-"$REPO_ROOT/.lab/qemu-cache"}
IMAGE_CONFIG="$LAB_DIR/config/image.yaml"
VM_CONFIG="$LAB_DIR/config/vm.yaml"
BASE_IMAGE="$CACHE_DIR/$(awk -F': ' '$1 == "image_id" {print $2}' "$IMAGE_CONFIG").img"
OVERLAY="$RUNTIME_DIR/overlay.qcow2"
SEED_IMAGE="$RUNTIME_DIR/seed.iso"
SSH_KEY="$RUNTIME_DIR/id_ed25519"
SSH_PUBLIC_KEY="$SSH_KEY.pub"
KNOWN_HOSTS="$RUNTIME_DIR/known_hosts"
PID_FILE="$RUNTIME_DIR/qemu.pid"
SERIAL_LOG="$RUNTIME_DIR/serial.log"
SSH_HOST=$(awk -F': ' '$1 == "ssh_host" {print $2}' "$VM_CONFIG")
SSH_PORT=$(awk -F': ' '$1 == "ssh_port" {print $2}' "$VM_CONFIG")
USERNAME=$(awk -F': ' '$1 == "username" {print $2}' "$VM_CONFIG")
VM_MEMORY=$(awk -F': ' '$1 == "memory_mb" {print $2}' "$VM_CONFIG")
VM_VCPUS=$(awk -F': ' '$1 == "vcpus" {print $2}' "$VM_CONFIG")
die() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "INFO: $*"; }
require_file() { [[ -f "$1" ]] || die "required file does not exist: $1"; }
ssh_common_args=(-i "$SSH_KEY" -p "$SSH_PORT" -o BatchMode=yes -o ConnectTimeout=3 -o StrictHostKeyChecking=no -o UserKnownHostsFile="$KNOWN_HOSTS")
lab_ssh() { ssh "${ssh_common_args[@]}" "$USERNAME@$SSH_HOST" "$@"; }
runtime_path_is_safe() {
  local root candidate
  root=$(realpath -m "$REPO_ROOT/.lab/qemu")
  candidate=$(realpath -m "$1")
  [[ "$candidate" == "$root" || "$candidate" == "$root"/* ]]
}
