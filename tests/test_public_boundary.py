import unittest

from validation.check_public_boundary import path_is_allowed


class PublicBoundaryTests(unittest.TestCase):
    def test_public_paths_are_allowed(self) -> None:
        allowed = (
            "README.md",
            "agent/diagnose.md",
            "docs/architecture.md",
            "knowledge/components/demo-api.service.yaml",
            "lab/qemu/scripts/boot.sh",
            "lab/scenarios/storage-001/inject.sh",
            "examples/runs/storage-001/manifest.yaml",
            "validation/validate_run.py",
        )
        for path in allowed:
            with self.subTest(path=path):
                self.assertTrue(path_is_allowed(path))

    def test_legacy_or_unscoped_paths_are_rejected(self) -> None:
        rejected = (
            "legacy-notes.md",
            "docs/roadmap.md",
            "knowledge/versions/example.yaml",
            "modules/example/manifest.yaml",
            "systems/example/state.yaml",
            "examples/runs/unreviewed/manifest.yaml",
            "lab/scenarios/unreviewed/inject.sh",
        )
        for path in rejected:
            with self.subTest(path=path):
                self.assertFalse(path_is_allowed(path))
