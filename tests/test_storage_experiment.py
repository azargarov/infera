from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

from validation.evaluate_storage import evaluate


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/runs/storage-001"


class StorageExperimentTests(unittest.TestCase):
    def _copy_example(self):
        temp = tempfile.TemporaryDirectory()
        run_dir = Path(temp.name) / "run"
        shutil.copytree(EXAMPLE, run_dir)
        return temp, run_dir

    def test_reviewed_example_passes(self) -> None:
        self.assertEqual(evaluate(EXAMPLE, ROOT)["result"], "pass")

    def test_injector_requires_explicit_id_and_local_target(self) -> None:
        injector = ROOT / "lab/scenarios/storage-001/inject.sh"
        result = subprocess.run([str(injector)], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)
        for name in ("inject.sh", "verify.sh", "prepare-run.sh"):
            text = (ROOT / "lab/scenarios/storage-001" / name).read_text()
            self.assertIn('SSH_HOST" == 127.0.0.1', text)

    def test_missing_storage_evidence_fails(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            path = run_dir / "evidence/records.yaml"
            records = yaml.safe_load(path.read_text())
            for record in records:
                record["observation_ids"] = [item for item in record["observation_ids"] if item != "affected_filesystem_near_full"]
            path.write_text(yaml.safe_dump(records, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_missing_application_evidence_fails(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            path = run_dir / "evidence/records.yaml"
            records = yaml.safe_load(path.read_text())
            for record in records:
                record["observation_ids"] = [item for item in record["observation_ids"] if item != "application_write_failure"]
            path.write_text(yaml.safe_dump(records, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_missing_comparison_evidence_fails(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            path = run_dir / "evidence/records.yaml"
            records = yaml.safe_load(path.read_text())
            for record in records:
                record["observation_ids"] = [item for item in record["observation_ids"] if item != "comparison_filesystem_healthy"]
            path.write_text(yaml.safe_dump(records, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_whole_host_claim_fails(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            path = run_dir / "findings/findings.yaml"
            findings = yaml.safe_load(path.read_text())
            findings[0]["status"] = "confirmed"
            findings[0]["statement"] = "The entire system is out of disk space."
            path.write_text(yaml.safe_dump(findings, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_cleanup_action_fails(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            (run_dir / "actions/actions.yaml").write_text("- action_id: delete-files\n")
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_agent_context_excludes_storage_answer_key(self) -> None:
        context = (EXAMPLE / "agent-context.yaml").read_text()
        self.assertNotIn("/srv/infera-data", context)
        self.assertNotIn("fill threshold", context)
        self.assertNotIn("expected conclusion", context)


if __name__ == "__main__":
    unittest.main()
