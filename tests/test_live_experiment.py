from pathlib import Path
import subprocess
import unittest

from validation.evaluate_service_failure import evaluate

ROOT = Path(__file__).resolve().parents[1]


class LiveExperimentContractTests(unittest.TestCase):
    def test_injector_requires_explicit_scenario_id(self) -> None:
        result = subprocess.run(
            [str(ROOT / "lab/scenarios/service-failure-001/inject.sh")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)

    def test_injector_and_verifier_require_local_lab_target(self) -> None:
        for name in ("inject.sh", "verify.sh", "prepare-run.sh"):
            text = (ROOT / "lab/scenarios/service-failure-001" / name).read_text()
            self.assertIn('SSH_HOST" == 127.0.0.1', text)
            self.assertIn("service-failure-001", text)

    def test_agent_context_excludes_evaluator_answer_fields(self) -> None:
        workflow = (ROOT / "agent/diagnose.md").read_text()
        self.assertIn("Do not read its injection", workflow)
        self.assertIn("Do not put interpretations", workflow)
        self.assertNotIn("dependency failure as the leading", workflow)

    def test_diagnostic_workflow_has_no_remediation_commands(self) -> None:
        workflow = (ROOT / "agent/diagnose.md").read_text().lower()
        self.assertIn("read_only", workflow)
        self.assertIn("do not restart, start, or stop services", workflow)
        self.assertIn("do not", workflow)

    def test_reviewed_example_evaluates_without_remediation(self) -> None:
        result = evaluate(ROOT / "examples/runs/service-failure-001", ROOT)
        self.assertEqual(result["result"], "pass")
        self.assertEqual(result["checks"]["safety"], "pass")


if __name__ == "__main__":
    unittest.main()
