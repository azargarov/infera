#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
source "$SCRIPT_DIR/common.sh"
"$SCRIPT_DIR/check-prereqs.sh" >/dev/null
URL=$(awk -F': ' '$1 == "source_url" {print $2}' "$IMAGE_CONFIG")
EXPECTED=$(awk -F': ' '$1 == "sha256" {print $2}' "$IMAGE_CONFIG")
[[ "$URL" == https://cloud-images.ubuntu.com/* ]] || die "image URL must use the official Ubuntu Cloud Images host"
[[ "$EXPECTED" =~ ^[0-9a-f]{64}$ ]] || die "image checksum is not a SHA-256 value"
mkdir -p "$CACHE_DIR"
if [[ -f "$BASE_IMAGE" ]]; then
  ACTUAL=$(sha256sum "$BASE_IMAGE" | awk '{print $1}')
  [[ "$ACTUAL" == "$EXPECTED" ]] && { info "verified cached base image: $BASE_IMAGE"; exit 0; }
  die "cached image checksum mismatch; remove only $BASE_IMAGE and retry"
fi
tmp="$BASE_IMAGE.partial"
rm -f "$tmp"
info "downloading pinned Ubuntu image"
curl --fail --location --retry 3 --output "$tmp" "$URL"
ACTUAL=$(sha256sum "$tmp" | awk '{print $1}')
if [[ "$ACTUAL" != "$EXPECTED" ]]; then rm -f "$tmp"; die "downloaded image checksum mismatch: expected $EXPECTED, got $ACTUAL"; fi
qemu-img info "$tmp" >/dev/null || { rm -f "$tmp"; die "downloaded file is not a readable QEMU image"; }
mv "$tmp" "$BASE_IMAGE"
info "verified base image: $BASE_IMAGE"
