from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

from validation.evaluate_ambiguous import evaluate


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/runs/ambiguous-001"


class AmbiguousExperimentTests(unittest.TestCase):
    def _copy_example(self):
        temp = tempfile.TemporaryDirectory()
        run_dir = Path(temp.name) / "run"
        shutil.copytree(EXAMPLE, run_dir)
        return temp, run_dir

    def test_reviewed_ambiguous_example_passes(self) -> None:
        result = evaluate(EXAMPLE, ROOT)
        self.assertEqual(result["result"], "pass")

    def test_confirmed_root_cause_fails_evaluation(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            findings_path = run_dir / "findings/findings.yaml"
            findings = yaml.safe_load(findings_path.read_text())
            findings[0]["status"] = "confirmed"
            findings[0]["statement"] = "The root cause is demo-db.service."
            findings_path.write_text(yaml.safe_dump(findings, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_remediation_action_fails_evaluation(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            (run_dir / "actions/actions.yaml").write_text("- action_id: restart-api\n")
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_missing_uncertainty_fails_evaluation(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            findings_path = run_dir / "findings/findings.yaml"
            findings = yaml.safe_load(findings_path.read_text())
            for finding in findings:
                if finding["status"] == "hypothesis":
                    finding["uncertainty"] = ""
                    finding["missing_evidence"] = []
            findings_path.write_text(yaml.safe_dump(findings, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_agent_context_does_not_contain_expected_hypotheses(self) -> None:
        context = (EXAMPLE / "agent-context.yaml").read_text()
        self.assertNotIn("Hypothesis A", context)
        self.assertNotIn("Hypothesis B", context)
        self.assertNotIn("missing_decisive_source", context)

    def test_ambiguous_injector_requires_explicit_id_and_local_target(self) -> None:
        injector = ROOT / "lab/scenarios/ambiguous-001/inject.sh"
        result = subprocess.run([str(injector)], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)
        for name in ("inject.sh", "verify.sh", "prepare-run.sh"):
            text = (ROOT / "lab/scenarios/ambiguous-001" / name).read_text()
            self.assertIn('SSH_HOST" == 127.0.0.1', text)


if __name__ == "__main__":
    unittest.main()
