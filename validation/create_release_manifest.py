#!/usr/bin/env python3
"""Create a small machine-readable manifest for a public Infera release."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


def git_value(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def build(version: str, commit: str | None = None) -> dict[str, Any]:
    image = yaml.safe_load((ROOT / "lab/qemu/config/image.yaml").read_text(encoding="utf-8"))
    return {
        "project": "Infera",
        "version": version,
        "commit": commit or git_value("rev-parse", "HEAD"),
        "supported_python": ">=3.11",
        "pinned_image": {
            "image_id": image["image_id"],
            "release": image["release"],
            "architecture": image["architecture"],
            "sha256": image["sha256"],
        },
        "reviewed_diagnostic_scenarios": [
            "service-failure-001",
            "ambiguous-001",
            "resource-pressure-001",
            "storage-001",
            "network-dependency-001",
        ],
        "reviewed_pm_scenarios": ["pm-restart-001"],
        "validation": {
            "offline_tests": "run by CI",
            "qemu_integration": "self-hosted KVM workflow",
            "agent_behavior": "manually reviewed; not automated in v0.1",
        },
        "known_limitations": [
            "experimental proof of concept",
            "synthetic Linux target only",
            "no production monitoring or autonomous remediation",
            "no hosted LLM provider integration",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(build(args.version, args.commit), sort_keys=False), encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
