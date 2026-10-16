#!/usr/bin/env python3
"""Scan tracked repository text for obvious public-boundary violations."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT_ALLOWLIST = {
    ".gitignore",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "pyproject.toml",
    "pytest.ini",
    "requirements-dev.txt",
    "requirements.txt",
}

EXACT_PATH_ALLOWLIST = {
    "agent/diagnose.md",
    "agent/pm-restart.md",
    "docs/architecture.md",
    "docs/ci-cd.md",
    "docs/github-metadata.md",
    "docs/limitations.md",
    "docs/release-checklist.md",
    "docs/sanitization-review.md",
    "knowledge/README.md",
    "knowledge/components/demo-api.service.yaml",
    "knowledge/components/demo-db.service.yaml",
    "knowledge/components/demo-upstream.service.yaml",
    "knowledge/patterns/dependency-failure.yaml",
    "knowledge/patterns/disk-pressure.yaml",
    "knowledge/patterns/restart-loop.yaml",
    "knowledge/system/expected-filesystems.yaml",
    "knowledge/system/expected-services.yaml",
    "knowledge/system/profile.yaml",
    "knowledge/system/resource-baseline.yaml",
    "scenarios/ambiguous-001.yaml",
    "scenarios/healthy-001.yaml",
    "scenarios/network-dependency-001.yaml",
    "scenarios/pm-restart-001.yaml",
    "scenarios/resource-pressure-001.yaml",
    "scenarios/service-failure-001.yaml",
    "scenarios/storage-001.yaml",
}

OPEN_PUBLIC_PREFIXES = (
    ".github/",
    "schemas/",
    "tests/",
    "validation/",
    "lab/qemu/",
)

SCOPED_PUBLIC_PREFIXES = (
    "examples/runs/ambiguous-001/",
    "examples/runs/network-dependency-001/",
    "examples/runs/pm-restart-001-approved/",
    "examples/runs/pm-restart-001-dry-run/",
    "examples/runs/resource-pressure-001/",
    "examples/runs/service-failure-001/",
    "examples/runs/storage-001/",
    "lab/scenarios/ambiguous-001/",
    "lab/scenarios/network-dependency-001/",
    "lab/scenarios/pm-restart-001/",
    "lab/scenarios/resource-pressure-001/",
    "lab/scenarios/service-failure-001/",
    "lab/scenarios/storage-001/",
)


def path_is_allowed(path: str) -> bool:
    return (
        path in ROOT_ALLOWLIST
        or path in EXACT_PATH_ALLOWLIST
        or path.startswith(OPEN_PUBLIC_PREFIXES)
        or path.startswith(SCOPED_PUBLIC_PREFIXES)
    )


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [root / item for item in result.stdout.decode().split("\0") if item]


def load_patterns(path: Path) -> list[tuple[int, re.Pattern[str]]]:
    patterns = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        patterns.append((line_number, re.compile(line, re.IGNORECASE)))
    return patterns


def scan(root: Path) -> list[str]:
    pattern_file = root / "validation/public-boundary-patterns.txt"
    patterns = load_patterns(pattern_file)
    path_pattern = re.compile(
        r"(^|/)(?:\.env(?:\..*)?|id_(?:rsa|ed25519|ecdsa)|known_hosts|[^/]+\.(?:pem|p12|pfx|key))$",
        re.IGNORECASE,
    )
    findings: list[str] = []
    for path in tracked_files(root):
        relative = path.relative_to(root)
        if not path_is_allowed(relative.as_posix()):
            findings.append(f"{relative}: path is outside the public repository allowlist")
        if path_pattern.search(relative.as_posix()):
            findings.append(f"{relative}: prohibited credential or environment filename")
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern_line, pattern in patterns:
            match = pattern.search(text)
            if match:
                findings.append(f"{relative}: pattern line {pattern_line}: {match.group(0)[:80]}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    findings = scan(args.root.resolve())
    if findings:
        print("PUBLIC-BOUNDARY CHECK FAILED")
        print("\n".join(findings))
        return 1
    print("PUBLIC-BOUNDARY CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
