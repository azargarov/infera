from pathlib import Path
import subprocess
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "lab" / "qemu"


class LabContractTests(unittest.TestCase):
    def test_pinned_image_metadata(self) -> None:
        image = yaml.safe_load((LAB / "config" / "image.yaml").read_text())
        self.assertEqual(image["architecture"], "amd64")
        self.assertTrue(image["source_url"].startswith("https://cloud-images.ubuntu.com/"))
        self.assertRegex(image["sha256"], r"^[0-9a-f]{64}$")

    def test_vm_metadata_and_cloud_init(self) -> None:
        vm = yaml.safe_load((LAB / "config" / "vm.yaml").read_text())
        self.assertEqual(vm["hostname"], "infera-lab")
        self.assertEqual(vm["network_mode"], "qemu-user")
        user_data = (LAB / "cloud-init" / "user-data").read_text()
        self.assertIn("__SSH_PUBLIC_KEY__", user_data)
        self.assertIn("demo-db.service", user_data)
        self.assertIn("demo-api.service", user_data)

    def test_shell_scripts_have_valid_syntax(self) -> None:
        for script in sorted((LAB / "scripts").glob("*.sh")):
            result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_runtime_path_is_ignored(self) -> None:
        result = subprocess.run(
            ["git", "check-ignore", "-q", "lab/qemu/runtime/overlay.qcow2"],
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
