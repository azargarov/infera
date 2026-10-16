from pathlib import Path
import unittest

import yaml

from validation.validate_knowledge import validate_document, validate_file


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "knowledge"
SCENARIO_IDS = {
    path.stem for path in (ROOT / "scenarios").glob("*.yaml")
}


class KnowledgeValidationTests(unittest.TestCase):
    def test_all_knowledge_entries_validate(self) -> None:
        paths = sorted(KNOWLEDGE_DIR.rglob("*.yaml"))
        self.assertEqual(len(paths), 10)
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(validate_file(path, SCENARIO_IDS), [])

    def test_knowledge_entry_ids_are_unique(self) -> None:
        entry_ids = []
        for path in sorted(KNOWLEDGE_DIR.rglob("*.yaml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
            entry_ids.append(document["entry_id"])
        self.assertEqual(len(entry_ids), len(set(entry_ids)))

    def test_learned_observation_requires_source(self) -> None:
        path = ROOT / "validation" / "fixtures" / "invalid" / "knowledge-no-source.yaml"
        errors = validate_file(path, SCENARIO_IDS)
        self.assertTrue(any("missing fields: source" in error for error in errors))

    def test_invalid_provenance_is_rejected(self) -> None:
        path = (
            ROOT
            / "validation"
            / "fixtures"
            / "invalid"
            / "knowledge-invalid-provenance.yaml"
        )
        errors = validate_file(path, SCENARIO_IDS)
        self.assertTrue(any("provenance is invalid" in error for error in errors))

    def test_scenario_answer_fields_are_rejected(self) -> None:
        path = (
            ROOT
            / "validation"
            / "fixtures"
            / "invalid"
            / "knowledge-scenario-answer.yaml"
        )
        errors = validate_file(path, SCENARIO_IDS)
        self.assertTrue(any("forbidden answer-key field" in error for error in errors))

    def test_scenario_id_references_are_rejected(self) -> None:
        document = yaml.safe_load(
            (
                ROOT
                / "knowledge"
                / "system"
                / "profile.yaml"
            ).read_text(encoding="utf-8")
        )
        document["content"]["note"] = "related to healthy-001"
        errors = validate_document(document, SCENARIO_IDS)
        self.assertTrue(any("references scenario ID" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
