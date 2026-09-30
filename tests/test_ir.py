"""Behavioral checks for the standalone architecture skill."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "skills" / "hardware-architecture-generator"


def invoke(skill: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(skill / "scripts" / "run.py"), *map(str, args)],
        cwd=cwd or ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class ArchitectureSkillTests(unittest.TestCase):
    def test_rejects_power_cycle_and_voltage_conflict(self):
        ir = json.loads((ARCHITECTURE / "references" / "architecture.json").read_text(encoding="utf-8"))
        ir["power_tree"]["rails"].append({"id": "V1V8", "source": "V3V3", "voltage_v": 1.8, "loads": []})
        ir["power_tree"]["rails"][0]["source"] = "V1V8"
        ir["pinmap"][0]["io_voltage_v"] = 1.8
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.json"
            path.write_text(json.dumps(ir), encoding="utf-8")
            result = invoke(ARCHITECTURE, "validate", path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("power_cycle", result.stdout)
        self.assertIn("io_voltage_conflict", result.stdout)

    def test_copied_skill_exports_without_repository_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            architecture = Path(shutil.copytree(ARCHITECTURE, root / "architecture"))
            result = invoke(architecture, "export", architecture / "references" / "architecture.json", "--out", root / "out", cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "out" / "power-tree.mmd").is_file())
            self.assertTrue((root / "out" / "pinmap.csv").is_file())


if __name__ == "__main__":
    unittest.main()
