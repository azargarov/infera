#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
RUN_ID=${1:-}
APPROVED_BY=${2:-}
[[ "$RUN_ID" =~ ^[a-z0-9]+(-[a-z0-9]+)*-[0-9]{8}T[0-9]{6}Z$ ]] || { echo "ERROR: usage: $0 <run-id> <approved-by>" >&2; exit 1; }
[[ -n "$APPROVED_BY" ]] || { echo "ERROR: approved-by is required" >&2; exit 1; }
[[ "$APPROVED_BY" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "ERROR: approved-by must be a simple identifier" >&2; exit 1; }
RUN_DIR="$REPO_ROOT/runs/$RUN_ID"
[[ -d "$RUN_DIR" ]] || { echo "ERROR: run directory does not exist: $RUN_DIR" >&2; exit 1; }
[[ ! -e "$RUN_DIR/actions/approval.yaml" ]] || { echo "ERROR: approval already exists" >&2; exit 1; }
cat > "$RUN_DIR/actions/approval.yaml" <<APPROVAL
schema_version: approval/v1
approval_id: approval-001
run_id: $RUN_ID
action_id: restart_demo_api
target: demo-api.service
approved_by: $APPROVED_BY
approved_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
decision: approved
APPROVAL
echo "Recorded explicit approval for restart_demo_api in $RUN_DIR/actions/approval.yaml"
