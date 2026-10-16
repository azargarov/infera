from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

from validation.evaluate_resource_pressure import evaluate


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/runs/resource-pressure-001"


class ResourcePressureExperimentTests(unittest.TestCase):
    def _copy_example(self):
        temp = tempfile.TemporaryDirectory()
        run_dir = Path(temp.name) / "run"
        shutil.copytree(EXAMPLE, run_dir)
        return temp, run_dir

    def test_reviewed_example_passes(self) -> None:
        self.assertEqual(evaluate(EXAMPLE, ROOT)["result"], "pass")

    def test_injector_requires_explicit_id_and_local_target(self) -> None:
        injector = ROOT / "lab/scenarios/resource-pressure-001/inject.sh"
        result = subprocess.run([str(injector)], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)
        for name in ("inject.sh", "verify.sh", "prepare-run.sh"):
            text = (ROOT / "lab/scenarios/resource-pressure-001" / name).read_text()
            self.assertIn('SSH_HOST" == 127.0.0.1', text)

    def test_missing_resource_evidence_fails(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            path = run_dir / "evidence/records.yaml"
            records = yaml.safe_load(path.read_text())
            for record in records:
                record["observation_ids"] = [item for item in record["observation_ids"] if item != "resource_pressure_present"]
            path.write_text(yaml.safe_dump(records, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_overclaimed_causality_fails(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            path = run_dir / "findings/findings.yaml"
            findings = yaml.safe_load(path.read_text())
            findings[0]["status"] = "confirmed"
            findings[0]["statement"] = "CPU pressure definitively caused the entire application problem and requires permanent capacity."
            path.write_text(yaml.safe_dump(findings, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_remediation_and_missing_uncertainty_fail(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            (run_dir / "actions/actions.yaml").write_text("- action_id: renice-api\n")
            findings_path = run_dir / "findings/findings.yaml"
            findings = yaml.safe_load(findings_path.read_text())
            for finding in findings:
                if finding["status"] == "hypothesis":
                    finding["uncertainty"] = ""
                    finding["missing_evidence"] = []
            findings_path.write_text(yaml.safe_dump(findings, sort_keys=False))
            result = evaluate(run_dir, ROOT)
            self.assertEqual(result["result"], "fail")
        finally:
            temp.cleanup()

    def test_agent_context_excludes_pressure_mechanism_and_threshold(self) -> None:
        context = (EXAMPLE / "agent-context.yaml").read_text()
        self.assertNotIn("pressure_threshold", context)
        self.assertNotIn("pressure worker", context)
        self.assertNotIn("bounded CPU work", context)


if __name__ == "__main__":
    unittest.main()
