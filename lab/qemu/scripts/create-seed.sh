#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
source "$SCRIPT_DIR/common.sh"
require_file "$LAB_DIR/cloud-init/user-data"
mkdir -p "$RUNTIME_DIR"
[[ -f "$SSH_KEY" ]] || ssh-keygen -q -t ed25519 -N '' -C infera-lab -f "$SSH_KEY"
rm -f "$SEED_IMAGE"
tmp_dir=$(mktemp -d "$RUNTIME_DIR/seed.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT
sed "s|__SSH_PUBLIC_KEY__|$(cat "$SSH_PUBLIC_KEY")|" "$LAB_DIR/cloud-init/user-data" > "$tmp_dir/user-data"
cp "$LAB_DIR/cloud-init/meta-data" "$tmp_dir/meta-data"
cp "$LAB_DIR/cloud-init/network-config" "$tmp_dir/network-config"
if command -v cloud-localds >/dev/null 2>&1; then
  cloud-localds --network-config="$tmp_dir/network-config" "$SEED_IMAGE" "$tmp_dir/user-data" "$tmp_dir/meta-data"
elif command -v xorriso >/dev/null 2>&1; then
  xorriso -as mkisofs -quiet -output "$SEED_IMAGE" -volid cidata -joliet -rock "$tmp_dir/user-data" "$tmp_dir/meta-data" "$tmp_dir/network-config"
else
  mkisofs -quiet -output "$SEED_IMAGE" -volid cidata -joliet -rock "$tmp_dir/user-data" "$tmp_dir/meta-data" "$tmp_dir/network-config"
fi
chmod 600 "$SSH_KEY" "$SSH_PUBLIC_KEY" "$SEED_IMAGE"
info "created cloud-init seed: $SEED_IMAGE"
