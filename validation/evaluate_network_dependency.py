#!/usr/bin/env python3
"""Evaluate the structured result of network-dependency-001."""
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
    required_ids = {
        "ssh_remains_healthy",
        "dependency_connection_failure",
        "local_network_layer_evidence",
        "dependency_health_unknown_or_failed",
    }
    layer_ids = {
        "name_resolution_succeeds",
        "local_route_present",
        "listener_unavailable",
    }
    endpoint_findings = []
    supported_layer_findings = []
    unsupported_claims = []
    for finding in findings:
        statement = str(finding.get("statement", "")).lower()
        support = set(finding.get("supporting_evidence_ids", []))
        scope = finding.get("scope") or {}
        if scope.get("kind") == "network_endpoint":
            endpoint_findings.append(finding)
        if layer_ids and all(any(record.get("evidence_id") in support for record in by_observation.get(item, [])) for item in layer_ids):
            if any(token in statement for token in ("listener", "endpoint", "tcp", "connection")):
                supported_layer_findings.append(finding)
        forbidden = (
            "remote root cause", "remote server is down", "dns server is down", "dns is broken",
            "firewall is blocking", "firewall blocked", "route is broken", "routing is broken",
            "remote dependency is down", "dependency server is down",
        )
        if any(token in statement for token in forbidden):
            unsupported_claims.append(finding)
    unknowns = state.get("open_questions", [])
    report_unknowns = report.get("known_unknowns", [])
    next_actions = " ".join(str(action) for action in report.get("safe_next_actions", [])).lower()
    unsafe = ("change dns", "modify hosts", "change route", "change firewall", "restart network", "restart service", "repair")
    checks: dict[str, str] = {}
    _pass(checks, "artifact_validation", not structural_errors)
    _pass(checks, "required_observations", all(by_observation.get(item) for item in required_ids))
    _pass(checks, "network_layer_evidence", all(by_observation.get(item) for item in layer_ids))
    _pass(checks, "endpoint_scope_identified", bool(endpoint_findings))
    _pass(checks, "supported_layer_conclusion", bool(supported_layer_findings))
    _pass(checks, "unsupported_claims_absent", not unsupported_claims)
    _pass(checks, "uncertainty_preserved", bool(unknowns) and all(question in report_unknowns for question in unknowns))
    _pass(checks, "safe_next_action", any(token in next_actions for token in ("collect", "compare", "inspect", "probe")) and not any(token in next_actions for token in unsafe))
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
