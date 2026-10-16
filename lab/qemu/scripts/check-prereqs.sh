#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
source "$SCRIPT_DIR/common.sh"
missing=()
for command in qemu-system-x86_64 qemu-img curl ssh ssh-keygen sha256sum awk; do
  command -v "$command" >/dev/null 2>&1 || missing+=("$command")
done
if ! command -v cloud-localds >/dev/null 2>&1 && ! command -v xorriso >/dev/null 2>&1 && ! command -v mkisofs >/dev/null 2>&1; then
  missing+=("cloud-localds or xorriso/mkisofs")
fi
((${#missing[@]} == 0)) || die "missing prerequisites: ${missing[*]}. Install QEMU, cloud-init seed tooling, OpenSSH client, curl, and coreutils using your distribution packages."
[[ "$(uname -m)" == "x86_64" ]] || die "the pinned image is amd64 and this host is $(uname -m)"
[[ -r /dev/kvm && -w /dev/kvm ]] || die "/dev/kvm is not usable; enable KVM or add your user to the kvm group"
mkdir -p "$CACHE_DIR" "$RUNTIME_DIR"
info "QEMU/KVM prerequisites are available"
