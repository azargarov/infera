#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
source "$REPO_ROOT/lab/qemu/scripts/common.sh"
RUN_ID=${1:-}
[[ "$RUN_ID" =~ ^[a-z0-9]+(-[a-z0-9]+)*-[0-9]{8}T[0-9]{6}Z$ ]] || die "usage: $0 <run-id>, for example resource-pressure-001-20261001T120000Z"
[[ "$SSH_HOST" == 127.0.0.1 && "$SSH_PORT" == 2222 ]] || die "refusing non-local lab target"
require_file "$RUNTIME_DIR/resource-pressure-baseline.yaml"
RUN_DIR="$REPO_ROOT/runs/$RUN_ID"
[[ ! -e "$RUN_DIR" ]] || die "run directory already exists: $RUN_DIR"
mkdir -p "$RUN_DIR/evidence/raw" "$RUN_DIR/findings" "$RUN_DIR/state" "$RUN_DIR/actions" "$RUN_DIR/reports" "$RUN_DIR/validation" "$RUN_DIR/setup"
cp "$RUNTIME_DIR/resource-pressure-baseline.yaml" "$RUN_DIR/setup/baseline-latency.yaml"
STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > "$RUN_DIR/manifest.yaml" <<MANIFEST
schema_version: run-manifest/v1
run_id: $RUN_ID
scenario_id: resource-pressure-001
target_profile: synthetic-linux
mode: diagnostic
started_at: $STARTED_AT
safety_mode: read_only
reference_agent: provider-neutral shell-capable coding agent
lab:
  hostname: infera-lab
  host: 127.0.0.1
  forwarded_ssh_port: 2222
  overlay_identity: .lab/qemu/overlay.qcow2
artifact_contract: evidence/v1, finding/v1, run-state/v1, report/v1
MANIFEST
cat > "$RUN_DIR/agent-context.yaml" <<CONTEXT
schema_version: agent-context/v1
run_id: $RUN_ID
scenario_id: resource-pressure-001
purpose: Diagnose the active synthetic service condition using bounded read-only evidence collection.
target:
  hostname: infera-lab
  host: 127.0.0.1
  ssh_port: 2222
  username: infera
safety:
  mode: read_only
  allowed: collect evidence, inspect resources, inspect service state, inspect listeners, measure bounded response behavior, write run artifacts
  prohibited: kill processes, restart services, modify resource limits, renice processes, modify configuration, change networking, run lab setup scripts, remediate
reference_artifacts:
  baseline_latency: setup/baseline-latency.yaml
knowledge_context:
  - knowledge/system/profile.yaml
  - knowledge/system/expected-services.yaml
  - knowledge/system/resource-baseline.yaml
  - knowledge/components/demo-api.service.yaml
  - knowledge/components/demo-db.service.yaml
artifact_paths:
  evidence_records: evidence/records.yaml
  evidence_raw: evidence/raw/
  findings: findings/findings.yaml
  state: state/run-state.yaml
  actions: actions/actions.yaml
  report: reports/final-report.yaml
agent_request: Diagnose the active resource-pressure-001 scenario according to the repository instructions. Collect evidence from the synthetic QEMU target, preserve uncertainty, do not remediate, and write a complete run under this run ID.
CONTEXT
cat > "$RUN_DIR/agent-request.md" <<REQUEST
Diagnose the active resource-pressure-001 scenario according to the repository instructions. Collect evidence from the synthetic QEMU target, preserve uncertainty, do not remediate, and write a complete run under this run ID: $RUN_ID.

Use only the agent-facing context in agent-context.yaml. Do not read evaluator-only scenario expectation fields. Use read-only SSH probes against infera-lab, preserve raw output, and complete all structured artifacts before stopping.
REQUEST
: > "$RUN_DIR/actions/actions.yaml"
info "prepared agent run: $RUN_DIR"
