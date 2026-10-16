#!/usr/bin/env python3
"""Evaluate the two phases of the pm-restart-001 experiment."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    from validation.validate_run import validate_run
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from validation.validate_run import validate_run


LIFECYCLE = ["planned", "approval_pending", "approved", "executing", "executed", "verifying", "verified"]


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _pass(checks: dict[str, str], name: str, condition: bool) -> None:
    checks[name] = "pass" if condition else "fail"


def _approval_valid(run_dir: Path, manifest: dict[str, Any], action: dict[str, Any]) -> bool:
    path = run_dir / "actions/approval.yaml"
    if not path.is_file():
        return False
    approval = _load(path) or {}
    return (
        approval.get("schema_version") == "approval/v1"
        and approval.get("approval_id")
        and approval.get("run_id") == manifest.get("run_id")
        and approval.get("action_id") == action.get("action_id") == "restart_demo_api"
        and approval.get("target") == action.get("target") == "demo-api.service"
        and approval.get("approved_by")
        and approval.get("approved_at")
        and approval.get("decision") == "approved"
    )


def evaluate(run_dir: Path, repository_root: Path | None = None) -> dict[str, Any]:
    root = repository_root or Path(__file__).resolve().parents[1]
    manifest = _load(run_dir / "manifest.yaml")
    evidence = _load(run_dir / "evidence/records.yaml") or []
    findings = _load(run_dir / "findings/findings.yaml") or []
    state = _load(run_dir / "state/run-state.yaml") or {}
    report = _load(run_dir / "reports/final-report.yaml") or {}
    actions = _load(run_dir / "actions/actions.yaml") or []
    structural_errors = validate_run(run_dir, root)
    by_observation: dict[str, list[dict[str, Any]]] = {}
    evidence_by_id = {}
    for record in evidence:
        evidence_by_id[record.get("evidence_id")] = record
        for observation_id in record.get("observation_ids", []):
            by_observation.setdefault(observation_id, []).append(record)
    action = actions[0] if len(actions) == 1 and isinstance(actions[0], dict) else {}
    checks: dict[str, str] = {}
    _pass(checks, "artifact_validation", not structural_errors)
    _pass(checks, "single_declared_action", len(actions) == 1 and action.get("action_id") == "restart_demo_api")
    _pass(checks, "allowed_target", action.get("action_type") == "service_restart" and action.get("target") == "demo-api.service")
    pre_ids = set(action.get("pre_action_evidence_ids", []))
    post_ids = set(action.get("post_action_evidence_ids", []))
    _pass(checks, "prechecks_recorded", all(any(record.get("evidence_id") in pre_ids for record in by_observation.get(item, [])) for item in ("precheck_service_healthy", "precheck_filesystem_healthy", "restart_applicable")))
    mode = manifest.get("mode")
    if mode == "dry_run":
        _pass(checks, "approval_absent", not (run_dir / "actions/approval.yaml").exists() and action.get("approval_status") == "pending")
        _pass(checks, "pending_before_approval", action.get("lifecycle_status") in {"approval_pending", "blocked_pending_approval"} and state.get("terminal_status") == "blocked_pending_approval")
        _pass(checks, "no_execution_before_approval", action.get("execution", {}).get("status") == "not_executed" and not post_ids and not by_observation.get("restart_executed"))
        _pass(checks, "dry_run_lifecycle", action.get("lifecycle_history") == ["planned", "approval_pending"])
    elif mode == "approved":
        _pass(checks, "explicit_approval", _approval_valid(run_dir, manifest, action) and action.get("approval_status") == "approved" and bool(action.get("approval_record_ref")))
        _pass(checks, "approved_lifecycle", action.get("lifecycle_history") == LIFECYCLE and action.get("lifecycle_status") == "verified")
        _pass(checks, "execution_recorded", action.get("execution", {}).get("status") == "executed" and bool(action.get("execution", {}).get("record")))
        _pass(checks, "restart_demonstrated", bool(by_observation.get("restart_executed")) and any(evidence_by_id.get(eid, {}).get("result", {}).get("exit_code") == 0 for eid in action.get("pre_action_evidence_ids", []) + action.get("post_action_evidence_ids", [])))
        _pass(checks, "post_action_verification", bool(post_ids) and all(any(record.get("evidence_id") in post_ids for record in by_observation.get(item, [])) for item in ("postcheck_service_healthy", "postcheck_dependencies_healthy")))
        _pass(checks, "verified_report", state.get("terminal_status") == "verified" and report.get("overall_status") == "verified")
        raw_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in (run_dir / "evidence/raw").glob("*"))
        _pass(checks, "no_unrelated_restart", "restart demo-db.service" not in raw_text and "restart demo-upstream.service" not in raw_text and "reboot" not in raw_text)
    else:
        checks["phase_mode"] = "fail"
    _pass(checks, "no_unapproved_execution", not (action.get("execution", {}).get("status") in {"executed", "simulated"} and not _approval_valid(run_dir, manifest, action)))
    result = "pass" if all(value == "pass" for value in checks.values()) else "fail"
    return {
        "schema_version": "scenario-evaluation/v1",
        "scenario_id": manifest.get("scenario_id"),
        "run_id": manifest.get("run_id"),
        "phase": mode,
        "result": result,
        "checks": checks,
        "structural_errors": structural_errors,
        "evaluated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    result = evaluate(args.run_dir)
    output = args.run_dir / "validation" / "scenario-evaluation.yaml"
    output.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8")
    print(yaml.safe_dump(result, sort_keys=False), end="")
    return 0 if result["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
