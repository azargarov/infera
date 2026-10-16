from pathlib import Path
import unittest

import yaml

from validation.validate_scenario import validate_document, validate_file


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = ROOT / "scenarios"


class ScenarioValidationTests(unittest.TestCase):
    def test_valid_scenario_files(self) -> None:
        paths = sorted(SCENARIO_DIR.glob("*.yaml"))
        paths.append(ROOT / "validation" / "fixtures" / "valid" / "minimal-valid.yaml")
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(validate_file(path), [])

    def test_scenario_ids_are_unique(self) -> None:
        ids = []
        for path in sorted(SCENARIO_DIR.glob("*.yaml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            ids.append(document["scenario_id"])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 7)

    def test_pm_scenario_has_approval_boundary(self) -> None:
        path = SCENARIO_DIR / "pm-restart-001.yaml"
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(document["safety"]["diagnostic_mode"], "read_only")
        self.assertEqual(document["safety"]["remediation_mode"], "approval_required")
        self.assertTrue(document["safety"]["approval_required"])
        self.assertTrue(document["pm"]["dry_run"]["required"])
        self.assertTrue(document["pm"]["approval"]["required"])
        self.assertTrue(document["pm"]["state_changing_actions"][0]["approval_required"])

    def test_non_pm_scenarios_do_not_declare_executable_remediation(self) -> None:
        for path in sorted(SCENARIO_DIR.glob("*.yaml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            if document["domain"] != "pm":
                self.assertNotEqual(
                    document["safety"]["remediation_mode"], "approval_required"
                )
                self.assertFalse(document["safety"]["approval_required"])

    def test_invalid_fixture_is_rejected(self) -> None:
        path = ROOT / "validation" / "fixtures" / "invalid" / "missing-reset.yaml"
        errors = validate_file(path)
        self.assertTrue(
            any("missing top-level fields: reset" in error for error in errors)
        )

    def test_mutating_injection_cannot_be_agent_allowed(self) -> None:
        path = ROOT / "validation" / "fixtures" / "valid" / "minimal-valid.yaml"
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document["injection"]["commands"] = [
            {
                "id": "bad-command",
                "command": "change-state",
                "mutates_target": True,
                "agent_allowed": True,
            }
        ]
        errors = validate_document(document)
        self.assertTrue(
            any("cannot allow an agent-mutating command" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
