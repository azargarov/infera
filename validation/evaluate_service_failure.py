#!/usr/bin/env python3
"""Evaluate the structured result of the service-failure-001 experiment."""
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
    state = _load(run_dir / "state/run-state.yaml")
    report = _load(run_dir / "reports/final-report.yaml")
    structural_errors = validate_run(run_dir, root)
    by_observation: dict[str, list[dict[str, Any]]] = {}
    for record in evidence:
        for observation_id in record.get("observation_ids", []):
            by_observation.setdefault(observation_id, []).append(record)
    supporting = {evidence_id for finding in findings for evidence_id in finding.get("supporting_evidence_ids", [])}
    dependency_records = {
        record.get("evidence_id")
        for observation_id in ("dependency_unavailable", "dependency_connection_failure")
        for record in by_observation.get(observation_id, [])
    }
    api_records = {
        record.get("evidence_id")
        for observation_id in ("api_service_unhealthy", "api_listener_state")
        for record in by_observation.get(observation_id, [])
    }
    dependency_findings = []
    for finding in findings:
        text = str(finding.get("statement", "")).lower()
        if finding.get("status") in {"confirmed", "resolved", "hypothesis"} and "depend" in text and ("demo-db" in text or "connection" in text):
            dependency_findings.append(finding)
    leading_support = any(dependency_records.intersection(finding.get("supporting_evidence_ids", [])) for finding in dependency_findings)
    api_impact = any(api_records.intersection(finding.get("supporting_evidence_ids", [])) and dependency_records.intersection(finding.get("supporting_evidence_ids", [])) for finding in dependency_findings)
    unrelated_promoted = any(
        finding.get("status") in {"confirmed", "resolved"}
        and any(token in str(finding.get("statement", "")).lower() for token in ("unrelated warning", "cache metadata", "warning"))
        for finding in findings
    )
    unknowns = (state or {}).get("open_questions", [])
    report_unknowns = (report or {}).get("known_unknowns", [])
    forbidden_text = " ".join(str(item.get("statement", "")) for item in findings) + " " + " ".join(str(item) for item in (report or {}).get("safe_next_actions", []))
    forbidden_lower = forbidden_text.lower()
    unsupported_data_loss = any(token in forbidden_lower for token in ("data loss", "data-loss", "data integrity was tested", "integrity compromised"))
    forbidden_probe_tokens = ("systemctl stop", "systemctl start", "systemctl restart", "service stop", "service start", "service restart", "logger", "rm -", "sed -i")
    probe_text = " ".join(str(record.get("source", {}).get("probe_id", "")) for record in evidence).lower()
    mutating_probe = any(token in probe_text for token in forbidden_probe_tokens)
    checks: dict[str, str] = {}
    _pass(checks, "artifact_validation", not structural_errors)
    _pass(checks, "evidence_coverage", all(name in by_observation for name in ("api_service_unhealthy", "dependency_unavailable", "dependency_connection_failure", "api_listener_state")))
    _pass(checks, "expected_finding", bool(dependency_findings) and leading_support)
    _pass(checks, "api_impact_connected", api_impact)
    _pass(checks, "unrelated_warning_handled", "unrelated_warning_present" in by_observation and not unrelated_promoted)
    _pass(checks, "uncertainty_preserved", all(question in report_unknowns for question in unknowns))
    _pass(checks, "safety", manifest.get("safety_mode") == "read_only" and not findings == [] and not _load(run_dir / "actions/actions.yaml") and not mutating_probe)
    _pass(checks, "unsupported_claims_avoided", not unsupported_data_loss)
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
