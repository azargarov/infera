#!/usr/bin/env python3
"""Structural validation for the public synthetic knowledge entries."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import yaml


REQUIRED_FIELDS = {
    "schema_version",
    "entry_id",
    "kind",
    "subject",
    "provenance",
    "review_status",
    "content",
    "source",
}
OPTIONAL_FIELDS = {"confidence", "observed_at"}
PROVENANCE_VALUES = {
    "baseline_fact",
    "documented_expectation",
    "learned_observation",
    "inferred_relationship",
    "unresolved_hypothesis",
}
KIND_VALUES = {"system", "component", "operational_pattern"}
REVIEW_VALUES = {"draft", "accepted"}
ANSWER_KEY_FIELDS = {"expected_root_cause", "expected_finding", "scenario_id"}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _contains_forbidden_key(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in ANSWER_KEY_FIELDS:
                return key
            found = _contains_forbidden_key(nested)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _contains_forbidden_key(item)
            if found:
                return found
    return None


def validate_document(
    document: Any, scenario_ids: Iterable[str] = ()
) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["document must be a mapping"]

    missing = REQUIRED_FIELDS - document.keys()
    unexpected = set(document) - REQUIRED_FIELDS - OPTIONAL_FIELDS
    if missing:
        errors.append(f"missing fields: {', '.join(sorted(missing))}")
    if unexpected:
        errors.append(f"unexpected fields: {', '.join(sorted(unexpected))}")

    if document.get("schema_version") != "knowledge-entry/v1":
        errors.append("schema_version must be knowledge-entry/v1")
    if not _nonempty_string(document.get("entry_id")):
        errors.append("entry_id must be a non-empty string")
    if document.get("kind") not in KIND_VALUES:
        errors.append("kind is invalid")
    if not _nonempty_string(document.get("subject")):
        errors.append("subject must be a non-empty string")
    if document.get("provenance") not in PROVENANCE_VALUES:
        errors.append("provenance is invalid")
    if document.get("review_status") not in REVIEW_VALUES:
        errors.append("review_status is invalid")
    if not isinstance(document.get("content"), dict):
        errors.append("content must be a mapping")

    source = document.get("source")
    if not isinstance(source, dict):
        errors.append("source must be a mapping")
    else:
        if not _nonempty_string(source.get("type")):
            errors.append("source.type must be a non-empty string")
        if not _nonempty_string(source.get("ref")):
            errors.append("source.ref must be a non-empty string")

    if "confidence" in document and document["confidence"] not in {
        "low",
        "medium",
        "high",
    }:
        errors.append("confidence is invalid")
    if "observed_at" in document and not _nonempty_string(document["observed_at"]):
        errors.append("observed_at must be a non-empty string")

    if document.get("provenance") in {
        "learned_observation",
        "inferred_relationship",
    } and not isinstance(source, dict):
        errors.append("learned and inferred entries require a source reference")

    forbidden_key = _contains_forbidden_key(document)
    if forbidden_key:
        errors.append(f"knowledge contains forbidden answer-key field: {forbidden_key}")

    serialized = yaml.safe_dump(document, sort_keys=True).lower()
    for scenario_id in scenario_ids:
        if scenario_id.lower() in serialized:
            errors.append(f"knowledge references scenario ID: {scenario_id}")

    return errors


def validate_file(path: Path, scenario_ids: Iterable[str] = ()) -> list[str]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        return [f"could not load YAML: {exc}"]
    return validate_document(document, scenario_ids)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entries", nargs="+", type=Path)
    parser.add_argument("--scenario-id", action="append", default=[])
    args = parser.parse_args()

    failed = False
    for path in args.entries:
        errors = validate_file(path, args.scenario_id)
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
