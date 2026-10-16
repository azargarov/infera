from pathlib import Path
import unittest

from validation.validate_run import validate_run


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "validation" / "fixtures" / "runs"


class RunValidationTests(unittest.TestCase):
    def test_valid_runs_pass(self) -> None:
        for name in ("healthy-valid", "service-failure-valid", "ambiguous-valid", "pm-dry-run-valid", "pm-approved-verified-valid"):
            with self.subTest(name=name):
                self.assertEqual(validate_run(RUNS / name, ROOT), [])

    def test_invalid_runs_fail_for_expected_reason(self) -> None:
        expected = {
            "invalid-missing-evidence": "references missing ID",
            "invalid-confirmed-no-evidence": "requires supporting evidence",
            "invalid-executed-no-approval": "requires approval evidence",
            "invalid-verified-no-post-evidence": "verified requires post-action evidence",
            "invalid-report-finding": "report finding_ids references missing ID",
            "invalid-identity-mismatch": "run state scenario_id does not match manifest",
            "invalid-unknown-dropped": "report known_unknowns drops",
            "invalid-dry-run-executed": "dry-run action restart-demo-api cannot be executed",
        }
        for name, fragment in expected.items():
            with self.subTest(name=name):
                errors = validate_run(RUNS / name, ROOT)
                self.assertTrue(errors)
                self.assertTrue(any(fragment in error for error in errors), errors)

    def test_scenario_observation_contract_is_checked(self) -> None:
        path = RUNS / "healthy-valid" / "evidence" / "records.yaml"
        original = path.read_text(encoding="utf-8")
        path.write_text(original.replace("target_reachable", "removed_observation", 1), encoding="utf-8")
        try:
            errors = validate_run(RUNS / "healthy-valid", ROOT)
            self.assertTrue(any("required scenario observation is missing" in error for error in errors))
        finally:
            path.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
