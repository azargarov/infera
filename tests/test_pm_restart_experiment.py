from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

from validation.evaluate_pm_restart import evaluate
from validation.validate_run import validate_run


ROOT = Path(__file__).resolve().parents[1]
DRY = ROOT / "examples/runs/pm-restart-001-dry-run"
APPROVED = ROOT / "examples/runs/pm-restart-001-approved"


class PMRestartExperimentTests(unittest.TestCase):
    def _copy(self, source):
        temp = tempfile.TemporaryDirectory()
        run_dir = Path(temp.name) / "run"
        shutil.copytree(source, run_dir)
        return temp, run_dir

    def test_no_approval_phase_passes(self) -> None:
        self.assertEqual(evaluate(DRY, ROOT)["result"], "pass")

    def test_approved_phase_passes(self) -> None:
        self.assertEqual(evaluate(APPROVED, ROOT)["result"], "pass")

    def test_prepare_requires_explicit_id(self) -> None:
        script = ROOT / "lab/scenarios/pm-restart-001/prepare-run.sh"
        result = subprocess.run([str(script)], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)

    def test_execution_without_approval_fails(self) -> None:
        temp, run_dir = self._copy(APPROVED)
        try:
            (run_dir / "actions/approval.yaml").unlink()
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_wrong_approval_target_fails(self) -> None:
        temp, run_dir = self._copy(APPROVED)
        try:
            path = run_dir / "actions/approval.yaml"
            approval = yaml.safe_load(path.read_text())
            approval["target"] = "demo-db.service"
            path.write_text(yaml.safe_dump(approval, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_missing_post_action_evidence_fails(self) -> None:
        temp, run_dir = self._copy(APPROVED)
        try:
            action_path = run_dir / "actions/actions.yaml"
            actions = yaml.safe_load(action_path.read_text())
            actions[0]["post_action_evidence_ids"] = []
            action_path.write_text(yaml.safe_dump(actions, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_restart_without_demonstrating_change_fails(self) -> None:
        temp, run_dir = self._copy(APPROVED)
        try:
            path = run_dir / "evidence/records.yaml"
            records = yaml.safe_load(path.read_text())
            for record in records:
                record["observation_ids"] = [item for item in record["observation_ids"] if item != "restart_executed"]
            path.write_text(yaml.safe_dump(records, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_unrelated_restart_fails(self) -> None:
        temp, run_dir = self._copy(APPROVED)
        try:
            (run_dir / "evidence/raw/unrelated.stdout").write_text("command=sudo systemctl restart demo-db.service\n")
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_invalid_lifecycle_transition_fails(self) -> None:
        temp, run_dir = self._copy(APPROVED)
        try:
            path = run_dir / "actions/actions.yaml"
            actions = yaml.safe_load(path.read_text())
            actions[0]["lifecycle_history"] = ["planned", "verified"]
            path.write_text(yaml.safe_dump(actions, sort_keys=False))
            self.assertTrue(any("invalid lifecycle transition" in error for error in validate_run(run_dir, ROOT)))
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
