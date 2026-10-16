from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

from validation.evaluate_network_dependency import evaluate


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/runs/network-dependency-001"


class NetworkDependencyExperimentTests(unittest.TestCase):
    def _copy_example(self):
        temp = tempfile.TemporaryDirectory()
        run_dir = Path(temp.name) / "run"
        shutil.copytree(EXAMPLE, run_dir)
        return temp, run_dir

    def test_reviewed_example_passes(self) -> None:
        self.assertEqual(evaluate(EXAMPLE, ROOT)["result"], "pass")

    def test_injector_requires_explicit_id_and_local_target(self) -> None:
        injector = ROOT / "lab/scenarios/network-dependency-001/inject.sh"
        result = subprocess.run([str(injector)], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr)
        for name in ("inject.sh", "verify.sh", "prepare-run.sh"):
            text = (ROOT / "lab/scenarios/network-dependency-001" / name).read_text()
            self.assertIn('SSH_HOST" == 127.0.0.1', text)

    def test_missing_network_evidence_fails(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            path = run_dir / "evidence/records.yaml"
            records = yaml.safe_load(path.read_text())
            for record in records:
                record["observation_ids"] = [item for item in record["observation_ids"] if item != "listener_unavailable"]
            path.write_text(yaml.safe_dump(records, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_wrong_layer_conclusion_fails(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            path = run_dir / "findings/findings.yaml"
            findings = yaml.safe_load(path.read_text())
            findings[0]["status"] = "confirmed"
            findings[0]["statement"] = "The DNS server is down and caused the remote root cause."
            path.write_text(yaml.safe_dump(findings, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_firewall_claim_fails(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            path = run_dir / "findings/findings.yaml"
            findings = yaml.safe_load(path.read_text())
            findings.append({**findings[0], "finding_id": "unsupported-firewall", "statement": "The firewall is blocking the dependency."})
            path.write_text(yaml.safe_dump(findings, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_remediation_and_missing_unknowns_fail(self) -> None:
        temp, run_dir = self._copy_example()
        try:
            (run_dir / "actions/actions.yaml").write_text("- action_id: change-firewall\n")
            state_path = run_dir / "state/run-state.yaml"
            state = yaml.safe_load(state_path.read_text())
            state["open_questions"] = []
            state_path.write_text(yaml.safe_dump(state, sort_keys=False))
            self.assertEqual(evaluate(run_dir, ROOT)["result"], "fail")
        finally:
            temp.cleanup()

    def test_agent_context_excludes_network_answer_key(self) -> None:
        context = (EXAMPLE / "agent-context.yaml").read_text()
        self.assertNotIn("listener unavailable", context)
        self.assertNotIn("network-dependency-active", context)
        self.assertNotIn("expected failed layer", context)


if __name__ == "__main__":
    unittest.main()
