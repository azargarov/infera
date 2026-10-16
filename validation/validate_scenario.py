#!/usr/bin/env python3
"""Structural validation for the Milestone 1 scenario contract."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml


TOP_LEVEL_REQUIRED = {
    "schema_version",
    "scenario_id",
    "title",
    "domain",
    "status",
    "purpose",
    "target",
    "initial_state",
    "injection",
    "expected_observations",
    "expected_reasoning",
    "known_unknowns",
    "safe_next_actions",
    "forbidden_behavior",
    "reset",
    "validation",
    "safety",
}

TOP_LEVEL_OPTIONAL = {"pm"}

SCENARIO_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-[0-9]{3}$")


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _required_mapping(
    value: Any, name: str, required: set[str], errors: list[str]
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be a mapping")
        return None
    missing = required - value.keys()
    if missing:
        errors.append(f"{name} is missing: {', '.join(sorted(missing))}")
    return value


def _nonempty_string_list(value: Any, name: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{name} must be a non-empty list")
        return
    for index, item in enumerate(value):
        if not _is_nonempty_string(item):
            errors.append(f"{name}[{index}] must be a non-empty string")


def _validate_pm_section(value: Any, errors: list[str]) -> None:
    required = {
        "pre_checks",
        "applicability",
        "dry_run",
        "approval",
        "state_changing_actions",
        "post_action_verification",
        "lifecycle_statuses",
    }
    pm = _required_mapping(value, "pm", required, errors)
    if not pm:
        return

    _nonempty_string_list(pm.get("pre_checks"), "pm.pre_checks", errors)
    if not _is_nonempty_string(pm.get("applicability")):
        errors.append("pm.applicability must be a non-empty string")
    _nonempty_string_list(
        pm.get("post_action_verification"),
        "pm.post_action_verification",
        errors,
    )
    _nonempty_string_list(
        pm.get("lifecycle_statuses"),
        "pm.lifecycle_statuses",
        errors,
    )

    dry_run = _required_mapping(
        pm.get("dry_run"),
        "pm.dry_run",
        {"required", "terminal_status"},
        errors,
    )
    if dry_run:
        if dry_run.get("required") is not True:
            errors.append("pm.dry_run.required must be true")
        if dry_run.get("terminal_status") != "approval_pending":
            errors.append("pm.dry_run.terminal_status must be approval_pending")

    approval = _required_mapping(
        pm.get("approval"),
        "pm.approval",
        {"required", "evidence", "status"},
        errors,
    )
    if approval:
        if approval.get("required") is not True:
            errors.append("pm.approval.required must be true")
        if not _is_nonempty_string(approval.get("evidence")):
            errors.append("pm.approval.evidence must be non-empty")
        if approval.get("status") != "approval_pending":
            errors.append("pm.approval.status must be approval_pending")

    actions = pm.get("state_changing_actions")
    if not isinstance(actions, list) or not actions:
        errors.append("pm.state_changing_actions must be a non-empty list")
    else:
        action_ids: set[str] = set()
        for index, action in enumerate(actions):
            item = _required_mapping(
                action,
                f"pm.state_changing_actions[{index}]",
                {"id", "operation", "approval_required"},
                errors,
            )
            if not item:
                continue
            action_id = item.get("id")
            if not _is_nonempty_string(action_id):
                errors.append(f"pm.state_changing_actions[{index}].id must be non-empty")
            elif action_id in action_ids:
                errors.append(f"duplicate PM action id: {action_id}")
            else:
                action_ids.add(action_id)
            if not _is_nonempty_string(item.get("operation")):
                errors.append(
                    f"pm.state_changing_actions[{index}].operation must be non-empty"
                )
            if item.get("approval_required") is not True:
                errors.append(
                    f"pm.state_changing_actions[{index}].approval_required must be true"
                )


def validate_document(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["document must be a mapping"]

    missing = TOP_LEVEL_REQUIRED - document.keys()
    unexpected = set(document) - TOP_LEVEL_REQUIRED - TOP_LEVEL_OPTIONAL
    if missing:
        errors.append(f"missing top-level fields: {', '.join(sorted(missing))}")
    if unexpected:
        errors.append(f"unexpected top-level fields: {', '.join(sorted(unexpected))}")

    if document.get("schema_version") != "scenario/v1":
        errors.append("schema_version must be scenario/v1")
    scenario_id = document.get("scenario_id")
    if not isinstance(scenario_id, str) or not SCENARIO_ID.fullmatch(scenario_id):
        errors.append("scenario_id must match the public scenario naming convention")
    if not _is_nonempty_string(document.get("title")):
        errors.append("title must be a non-empty string")
    valid_domains = {
        "baseline",
        "ambiguity",
        "service",
        "resource",
        "storage",
        "network",
        "pm",
    }
    if document.get("domain") not in valid_domains:
        errors.append("domain is invalid")
    if document.get("status") not in {"active", "draft"}:
        errors.append("status must be active or draft")
    if not _is_nonempty_string(document.get("purpose")):
        errors.append("purpose must be a non-empty string")

    target = _required_mapping(
        document.get("target"),
        "target",
        {"profile", "baseline", "reset"},
        errors,
    )
    if target:
        if target.get("profile") != "synthetic-linux":
            errors.append("target.profile must be synthetic-linux")
        if not _is_nonempty_string(target.get("baseline")):
            errors.append("target.baseline must be a non-empty string")
        if target.get("reset") not in {"disposable_overlay", "fixture_reset"}:
            errors.append("target.reset is invalid")

    initial = _required_mapping(
        document.get("initial_state"),
        "initial_state",
        {"expected", "injected_faults"},
        errors,
    )
    if initial:
        _nonempty_string_list(initial.get("expected"), "initial_state.expected", errors)
        if not isinstance(initial.get("injected_faults"), list):
            errors.append("initial_state.injected_faults must be a list")

    injection = _required_mapping(
        document.get("injection"),
        "injection",
        {"mode", "commands", "completion_check"},
        errors,
    )
    if injection:
        if injection.get("mode") not in {"none", "setup_only"}:
            errors.append("injection.mode is invalid")
        commands = injection.get("commands")
        if not isinstance(commands, list):
            errors.append("injection.commands must be a list")
        else:
            command_ids: set[str] = set()
            for index, command in enumerate(commands):
                item = _required_mapping(
                    command,
                    f"injection.commands[{index}]",
                    {"id", "command", "mutates_target", "agent_allowed"},
                    errors,
                )
                if not item:
                    continue
                command_id = item.get("id")
                if not _is_nonempty_string(command_id):
                    errors.append(f"injection.commands[{index}].id must be non-empty")
                elif command_id in command_ids:
                    errors.append(f"duplicate injection command id: {command_id}")
                else:
                    command_ids.add(command_id)
                if not _is_nonempty_string(item.get("command")):
                    errors.append(f"injection.commands[{index}].command must be non-empty")
                if not isinstance(item.get("mutates_target"), bool):
                    errors.append(
                        f"injection.commands[{index}].mutates_target must be boolean"
                    )
                if not isinstance(item.get("agent_allowed"), bool):
                    errors.append(
                        f"injection.commands[{index}].agent_allowed must be boolean"
                    )
                if item.get("mutates_target") and item.get("agent_allowed"):
                    errors.append(
                        f"injection.commands[{index}] cannot allow an agent-mutating command"
                    )
        completion = _required_mapping(
            injection.get("completion_check"),
            "injection.completion_check",
            {"type", "expected"},
            errors,
        )
        if completion:
            if completion.get("type") not in {"none", "manifest"}:
                errors.append("injection.completion_check.type is invalid")
            if not _is_nonempty_string(completion.get("expected")):
                errors.append("injection.completion_check.expected must be non-empty")

    observations = document.get("expected_observations")
    observation_ids: set[str] = set()
    if not isinstance(observations, list) or not observations:
        errors.append("expected_observations must be a non-empty list")
    else:
        for index, observation in enumerate(observations):
            item = _required_mapping(
                observation,
                f"expected_observations[{index}]",
                {"id", "source", "condition"},
                errors,
            )
            if not item:
                continue
            observation_id = item.get("id")
            if not _is_nonempty_string(observation_id):
                errors.append(f"expected_observations[{index}].id must be non-empty")
            elif observation_id in observation_ids:
                errors.append(f"duplicate observation id: {observation_id}")
            else:
                observation_ids.add(observation_id)
            for field in ("source", "condition"):
                if not _is_nonempty_string(item.get(field)):
                    errors.append(f"expected_observations[{index}].{field} must be non-empty")

    reasoning = _required_mapping(
        document.get("expected_reasoning"),
        "expected_reasoning",
        {"required", "forbidden_claims"},
        errors,
    )
    if reasoning:
        _nonempty_string_list(reasoning.get("required"), "expected_reasoning.required", errors)
        _nonempty_string_list(
            reasoning.get("forbidden_claims"),
            "expected_reasoning.forbidden_claims",
            errors,
        )

    _nonempty_string_list(document.get("known_unknowns"), "known_unknowns", errors)
    _nonempty_string_list(document.get("safe_next_actions"), "safe_next_actions", errors)
    _nonempty_string_list(document.get("forbidden_behavior"), "forbidden_behavior", errors)

    reset = _required_mapping(
        document.get("reset"), "reset", {"strategy", "procedure"}, errors
    )
    if reset:
        if reset.get("strategy") not in {"fixture_reset", "disposable_overlay"}:
            errors.append("reset.strategy is invalid")
        if not _is_nonempty_string(reset.get("procedure")):
            errors.append("reset.procedure must be non-empty")

    validation = _required_mapping(
        document.get("validation"),
        "validation",
        {"required_status", "required_observation_ids"},
        errors,
    )
    if validation:
        if not _is_nonempty_string(validation.get("required_status")):
            errors.append("validation.required_status must be non-empty")
        required_ids = validation.get("required_observation_ids")
        _nonempty_string_list(required_ids, "validation.required_observation_ids", errors)
        if isinstance(required_ids, list):
            for observation_id in required_ids:
                if observation_id not in observation_ids:
                    errors.append(
                        f"validation references unknown observation: {observation_id}"
                    )

    safety = _required_mapping(
        document.get("safety"),
        "safety",
        {"diagnostic_mode", "remediation_mode", "approval_required"},
        errors,
    )
    if safety:
        if safety.get("diagnostic_mode") != "read_only":
            errors.append("safety.diagnostic_mode must be read_only")
        if safety.get("remediation_mode") not in {
            "not_applicable",
            "dry_run_only",
            "approval_required",
        }:
            errors.append("safety.remediation_mode is invalid")
        if not isinstance(safety.get("approval_required"), bool):
            errors.append("safety.approval_required must be boolean")
        if document.get("domain") == "pm":
            if safety.get("remediation_mode") != "approval_required":
                errors.append("PM scenario must declare approval_required remediation")
            if safety.get("approval_required") is not True:
                errors.append("PM scenario must require approval")
        elif safety.get("remediation_mode") == "approval_required" or safety.get(
            "approval_required"
        ):
            errors.append("diagnostic scenarios cannot declare executable approval-required remediation")

    if document.get("domain") == "pm":
        _validate_pm_section(document.get("pm"), errors)
    elif "pm" in document:
        errors.append("only PM scenarios may contain a pm section")

    return errors


def validate_file(path: Path) -> list[str]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        return [f"could not load YAML: {exc}"]
    return validate_document(document)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenarios", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.scenarios:
        errors = validate_file(path)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"PASS {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
