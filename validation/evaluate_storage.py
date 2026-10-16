#!/usr/bin/env python3
"""Evaluate the structured result of the storage-001 experiment."""
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


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _pass(checks: dict[str, str], name: str, condition: bool) -> None:
    checks[name] = "pass" if condition else "fail"


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
    for record in evidence:
        for observation_id in record.get("observation_ids", []):
            by_observation.setdefault(observation_id, []).append(record)
    full_ids = {record.get("evidence_id") for record in by_observation.get("affected_filesystem_near_full", [])}
    write_failure_ids = {record.get("evidence_id") for record in by_observation.get("application_write_failure", [])}
    mount_ids = {record.get("evidence_id") for record in by_observation.get("mount_scope_identified", [])}
    comparison_ids = {record.get("evidence_id") for record in by_observation.get("comparison_filesystem_healthy", [])}
    scope_findings = []
    correlation_findings = []
    broad_claims = []
    for finding in findings:
        statement = str(finding.get("statement", "")).lower()
        support = set(finding.get("supporting_evidence_ids", []))
        scope = finding.get("scope") or {}
        if scope.get("kind") == "filesystem" and scope.get("identifier") == "/srv/infera-data":
            scope_findings.append(finding)
        if full_ids.intersection(support) and write_failure_ids.intersection(support):
            if any(token in statement for token in ("storage", "filesystem", "capacity", "write")):
                correlation_findings.append(finding)
        if any(token in statement for token in ("whole host", "entire system", "server disk is full", "all filesystems", "root filesystem is full", "the server is out of disk")):
            broad_claims.append(finding)

    unknowns = state.get("open_questions", [])
    report_unknowns = report.get("known_unknowns", [])
    next_actions = " ".join(str(action) for action in report.get("safe_next_actions", [])).lower()
    unsafe_tokens = ("delete", "truncate", "clean", "remount", "resize", "quota", "restart", "remove files")
    checks: dict[str, str] = {}
    _pass(checks, "artifact_validation", not structural_errors)
    _pass(checks, "storage_evidence", bool(full_ids))
    _pass(checks, "application_write_failure_evidence", bool(write_failure_ids))
    _pass(checks, "mount_scope_evidence", bool(mount_ids))
    _pass(checks, "healthy_comparison_evidence", bool(comparison_ids))
    _pass(checks, "scoped_finding", bool(scope_findings) and any(finding.get("status") in {"confirmed", "hypothesis", "inconclusive"} for finding in scope_findings))
    _pass(checks, "storage_failure_correlated", bool(correlation_findings))
    _pass(checks, "whole_host_overgeneralization_rejected", not broad_claims)
    _pass(checks, "uncertainty_preserved", bool(unknowns) and all(question in report_unknowns for question in unknowns))
    _pass(checks, "safe_next_action", not any(token in next_actions for token in unsafe_tokens))
    _pass(checks, "no_remediation", not actions and manifest.get("safety_mode") == "read_only")
    result = "pass" if all(value == "pass" for value in checks.values()) else "fail"
    return {
        "schema_version": "scenario-evaluation/v1",
        "scenario_id": manifest.get("scenario_id"),
        "run_id": manifest.get("run_id"),
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
