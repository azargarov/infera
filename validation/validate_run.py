#!/usr/bin/env python3
"""Validate a synthetic Infera run and its cross-artifact references."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    from validation.validate_scenario import validate_file as validate_scenario_file
except ModuleNotFoundError:  # Direct execution from the validation directory.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from validation.validate_scenario import validate_file as validate_scenario_file


def _load(path: Path, errors: list[str]) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"{path}: cannot load YAML: {exc}")
        return None


def _required(run_dir: Path, relative: str, errors: list[str]) -> Any:
    path = run_dir / relative
    if not path.is_file():
        errors.append(f"missing required artifact: {relative}")
        return None
    return _load(path, errors)


def _items(value: Any, name: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        errors.append(f"{name} must be a list of mappings")
        return []
    return value


def _same_identity(item: dict[str, Any], run_id: str, scenario_id: str, name: str, errors: list[str]) -> None:
    if item.get("run_id") != run_id:
        errors.append(f"{name} run_id does not match manifest")
    if item.get("scenario_id") != scenario_id:
        errors.append(f"{name} scenario_id does not match manifest")


def _refs_exist(refs: Any, known: set[str], name: str, errors: list[str]) -> None:
    if not isinstance(refs, list):
        errors.append(f"{name} must be a list")
        return
    for ref in refs:
        if ref not in known:
            errors.append(f"{name} references missing ID: {ref}")


def _safe_artifact_ref(run_dir: Path, ref: Any, name: str, errors: list[str]) -> None:
    if not isinstance(ref, str) or not ref:
        errors.append(f"{name} must be a non-empty relative path")
        return
    path = Path(ref)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{name} must stay inside the run directory")
    elif not (run_dir / path).is_file():
        errors.append(f"{name} does not resolve: {ref}")


def validate_run(run_dir: Path, repository_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    manifest = _required(run_dir, "manifest.yaml", errors)
    if not isinstance(manifest, dict):
        return errors
    if manifest.get("schema_version") != "run-manifest/v1":
        errors.append("manifest schema_version must be run-manifest/v1")
    run_id = manifest.get("run_id")
    scenario_id = manifest.get("scenario_id")
    if not isinstance(run_id, str) or not run_id:
        errors.append("manifest run_id must be non-empty")
    if not isinstance(scenario_id, str) or not scenario_id:
        errors.append("manifest scenario_id must be non-empty")
    if manifest.get("target_profile") != "synthetic-linux":
        errors.append("manifest target_profile must be synthetic-linux")
    mode = manifest.get("mode")
    if mode not in {"diagnostic", "dry_run", "approved"}:
        errors.append("manifest mode is invalid")
    if not isinstance(run_id, str) or not isinstance(scenario_id, str):
        return errors

    root = repository_root or Path(__file__).resolve().parents[1]
    scenario_path = root / "scenarios" / f"{scenario_id}.yaml"
    if not scenario_path.is_file():
        errors.append(f"scenario manifest does not exist: {scenario_id}")
        scenario = {}
    else:
        scenario_errors = validate_scenario_file(scenario_path)
        errors.extend(f"scenario {scenario_id}: {error}" for error in scenario_errors)
        scenario = _load(scenario_path, errors) or {}

    evidence = _items(_required(run_dir, "evidence/records.yaml", errors), "evidence", errors)
    findings = _items(_required(run_dir, "findings/findings.yaml", errors), "findings", errors)
    actions = _items(_required(run_dir, "actions/actions.yaml", errors), "actions", errors)
    state = _required(run_dir, "state/run-state.yaml", errors)
    report = _required(run_dir, "reports/final-report.yaml", errors)
    validation = _required(run_dir, "validation/validation-result.yaml", errors)

    evidence_ids: set[str] = set()
    for item in evidence:
        _same_identity(item, run_id, scenario_id, f"evidence {item.get('evidence_id', '<unknown>')}", errors)
        evidence_id = item.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            errors.append("evidence must have a non-empty evidence_id")
        elif evidence_id in evidence_ids:
            errors.append(f"duplicate evidence_id: {evidence_id}")
        else:
            evidence_ids.add(evidence_id)
        source = item.get("source")
        result = item.get("result")
        if not isinstance(source, dict) or not source.get("type") or not source.get("target"):
            errors.append(f"evidence {evidence_id} has incomplete source")
        if not isinstance(result, dict) or not isinstance(result.get("exit_code"), int):
            errors.append(f"evidence {evidence_id} has incomplete result")
        else:
            for key in ("stdout_ref", "stderr_ref"):
                _safe_artifact_ref(run_dir, result.get(key), f"evidence {evidence_id} {key}", errors)
        if item.get("observation_status") not in {"observed", "unavailable"}:
            errors.append(f"evidence {evidence_id} observation_status is invalid")
        if not isinstance(item.get("observation_ids", []), list):
            errors.append(f"evidence {evidence_id} observation_ids must be a list")

    knowledge_ids: set[str] = set()
    for path in sorted((root / "knowledge").rglob("*.yaml")):
        document = _load(path, errors)
        if isinstance(document, dict) and isinstance(document.get("entry_id"), str):
            knowledge_ids.add(document["entry_id"])

    finding_ids: set[str] = set()
    for item in findings:
        finding_id = item.get("finding_id")
        _same_identity(item, run_id, scenario_id, f"finding {finding_id or '<unknown>'}", errors)
        if not isinstance(finding_id, str) or not finding_id:
            errors.append("finding must have a non-empty finding_id")
        elif finding_id in finding_ids:
            errors.append(f"duplicate finding_id: {finding_id}")
        else:
            finding_ids.add(finding_id)
        _refs_exist(item.get("supporting_evidence_ids", []), evidence_ids, f"finding {finding_id} supporting_evidence_ids", errors)
        _refs_exist(item.get("conflicting_evidence_ids", []), evidence_ids, f"finding {finding_id} conflicting_evidence_ids", errors)
        _refs_exist(item.get("related_knowledge_ids", []), knowledge_ids, f"finding {finding_id} related_knowledge_ids", errors)
        status = item.get("status")
        if status not in {"observed", "hypothesis", "confirmed", "inconclusive", "resolved"}:
            errors.append(f"finding {finding_id} status is invalid")
        if status in {"confirmed", "resolved"} and not item.get("supporting_evidence_ids"):
            errors.append(f"finding {finding_id} {status} requires supporting evidence")
        if status in {"hypothesis", "inconclusive"} and not (item.get("uncertainty") or item.get("missing_evidence")):
            errors.append(f"finding {finding_id} must preserve uncertainty or missing evidence")

    action_ids: set[str] = set()
    for item in actions:
        action_id = item.get("action_id")
        _same_identity(item, run_id, scenario_id, f"action {action_id or '<unknown>'}", errors)
        if not isinstance(action_id, str) or not action_id:
            errors.append("action must have a non-empty action_id")
        elif action_id in action_ids:
            errors.append(f"duplicate action_id: {action_id}")
        else:
            action_ids.add(action_id)
        _refs_exist(item.get("pre_action_evidence_ids", []), evidence_ids, f"action {action_id} pre_action_evidence_ids", errors)
        _refs_exist(item.get("post_action_evidence_ids", []), evidence_ids, f"action {action_id} post_action_evidence_ids", errors)
        status = item.get("lifecycle_status")
        approval_required = item.get("approval_required") is True
        approval_status = item.get("approval_status")
        if status not in {"planned", "approval_pending", "approved", "executing", "executed", "verifying", "verified", "skipped", "blocked_pending_approval", "failed"}:
            errors.append(f"action {action_id} lifecycle_status is invalid")
        if approval_required and status in {"approved", "executing", "executed", "verifying", "verified"}:
            if approval_status != "approved" or not item.get("approval_record_ref"):
                errors.append(f"action {action_id} requires approval evidence before execution")
            else:
                _safe_artifact_ref(run_dir, item["approval_record_ref"], f"action {action_id} approval_record_ref", errors)
        if status in {"executed", "verifying", "verified"} and approval_status != "approved":
            errors.append(f"action {action_id} cannot be {status} without approval")
        if status == "executed" and item.get("execution", {}).get("status") not in {"simulated", "executed"}:
            errors.append(f"action {action_id} executed requires an execution record")
        if status == "verified" and not item.get("post_action_evidence_ids"):
            errors.append(f"action {action_id} verified requires post-action evidence")
        if status == "failed" and not item.get("failure_details"):
            errors.append(f"action {action_id} failed requires failure_details")
        history = item.get("lifecycle_history")
        if history is not None:
            allowed_transitions = {
                "planned": {"approval_pending", "skipped", "failed"},
                "approval_pending": {"approved", "blocked_pending_approval", "failed"},
                "approved": {"executing", "failed"},
                "executing": {"executed", "failed"},
                "executed": {"verifying", "failed"},
                "verifying": {"verified", "failed"},
                "verified": set(),
                "skipped": set(),
                "blocked_pending_approval": set(),
                "failed": set(),
            }
            if not isinstance(history, list) or not history:
                errors.append(f"action {action_id} lifecycle_history must be a non-empty list")
            elif history[-1] != status:
                errors.append(f"action {action_id} lifecycle_history must end at lifecycle_status")
            else:
                for previous, current in zip(history, history[1:]):
                    if current not in allowed_transitions.get(previous, set()):
                        errors.append(f"action {action_id} invalid lifecycle transition: {previous} -> {current}")
        if mode == "dry_run" and status in {"executed", "verifying", "verified"}:
            errors.append(f"dry-run action {action_id} cannot be {status}")

    if isinstance(state, dict):
        _same_identity(state, run_id, scenario_id, "run state", errors)
        if state.get("phase") not in {"initialized", "collecting", "reasoning", "report_ready", "validation_complete", "blocked_pending_approval", "failed"}:
            errors.append("run state phase is invalid")
        if state.get("safety_mode") not in {"read_only", "dry_run", "approved"}:
            errors.append("run state safety_mode is invalid")
        if state.get("phase") == "validation_complete" and not isinstance(validation, dict):
            errors.append("validation_complete requires a validation result")
        if state.get("phase") == "blocked_pending_approval" and any(a.get("lifecycle_status") in {"executed", "verified"} for a in actions):
            errors.append("blocked approval state cannot contain an executed PM action")

    if isinstance(report, dict):
        _same_identity(report, run_id, scenario_id, "report", errors)
        _refs_exist(report.get("finding_ids", []), finding_ids, "report finding_ids", errors)
        _refs_exist(report.get("evidence_ids", []), evidence_ids, "report evidence_ids", errors)
        report_action_ids = {item.get("action_id"): item.get("status") for item in report.get("action_refs", []) if isinstance(item, dict)}
        for action in actions:
            if report_action_ids.get(action.get("action_id")) != action.get("lifecycle_status"):
                errors.append(f"report action reference does not match action {action.get('action_id')}")
        open_questions = (state or {}).get("open_questions", []) if isinstance(state, dict) else []
        if not isinstance(report.get("known_unknowns"), list) or any(q not in report["known_unknowns"] for q in open_questions):
            errors.append("report known_unknowns drops an open run-state question")
        if isinstance(state, dict) and report.get("overall_status") != state.get("terminal_status"):
            errors.append("report overall_status does not match run-state terminal_status")
        if isinstance(validation, dict) and report.get("validation_status") != validation.get("status"):
            errors.append("report validation_status does not match validation result")

    if isinstance(validation, dict):
        if validation.get("run_id") != run_id:
            errors.append("validation result run_id does not match manifest")
        if validation.get("status") != "passed":
            errors.append("validation result status must be passed")

    required_observations = set((scenario.get("validation") or {}).get("required_observation_ids", []))
    observed = {observation_id for item in evidence for observation_id in item.get("observation_ids", [])}
    for observation_id in sorted(required_observations - observed):
        if (
            scenario.get("domain") == "pm"
            and mode == "dry_run"
            and observation_id == "postcheck_service_healthy"
        ):
            continue
        errors.append(f"required scenario observation is missing: {observation_id}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for run_dir in args.run_dirs:
        errors = validate_run(run_dir)
        if errors:
            failed = True
            print(f"FAIL {run_dir}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {run_dir}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
