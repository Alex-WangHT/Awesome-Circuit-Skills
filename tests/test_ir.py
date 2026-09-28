"""Checks for engineering invariants and deterministic adapter output."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from circuit_skills.adapters.kicad import KiCadAdapter
from circuit_skills.validation import validate


ROOT = Path(__file__).resolve().parents[1]


def fixture(name: str) -> dict:
    skill = "eda-component-generator" if name == "component.json" else "hardware-architecture-generator"
    return json.loads((ROOT / "skills" / skill / "references" / name).read_text(encoding="utf-8"))


class IRTests(unittest.TestCase):
    def test_component_pin_pad_mismatch_is_error(self):
        ir = fixture("component.json")
        ir["footprint"]["pads"][3]["number"] = "5"
        report = validate(ir)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("pin_pad_mismatch", {item["code"] for item in report["issues"]})

    def test_component_rejects_overlap_and_missing_evidence(self):
        ir = fixture("component.json")
        ir["footprint"]["pads"][1]["x_mm"] = -0.75
        ir["footprint"]["pads"][1]["y_mm"] = -0.75
        ir["pins"][0]["source"] = ""
        report = validate(ir)
        codes = {item["code"] for item in report["issues"]}
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("pad_overlap", codes)
        self.assertIn("required_text", codes)

    def test_architecture_rejects_cycle_and_voltage_conflict(self):
        ir = fixture("architecture.json")
        ir["power_tree"]["rails"].append({"id": "V1V8", "source": "V3V3", "voltage_v": 1.8, "loads": []})
        ir["power_tree"]["rails"][0]["source"] = "V1V8"
        ir["pinmap"][0]["io_voltage_v"] = 1.8
        report = validate(ir)
        codes = {item["code"] for item in report["issues"]}
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("power_cycle", codes)
        self.assertIn("io_voltage_conflict", codes)

    @unittest.skipIf(importlib.util.find_spec("OCP") is None, "STEP runtime not installed")
    def test_adapter_exports_readable_step(self):
        ir = fixture("component.json")
        self.assertEqual(validate(ir)["status"], "PASS")
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "one"
            second = Path(temp) / "two"
            adapter = KiCadAdapter()
            adapter.export_component(ir, first)
            adapter.export_component(copy.deepcopy(ir), second)
            for relative in (
                "AwesomeCircuit.kicad_sym",
                "AwesomeCircuit.pretty/EX_QFN4.kicad_mod",
            ):
                self.assertEqual((first / relative).read_bytes(), (second / relative).read_bytes())
            step = first / "AwesomeCircuit.3dshapes/EX_QFN4.step"
            self.assertTrue(step.read_bytes().startswith(b"ISO-10303-21;"))
            self.assertIn('../AwesomeCircuit.3dshapes/EX_QFN4.step', (first / "AwesomeCircuit.pretty/EX_QFN4.kicad_mod").read_text(encoding="utf-8"))
            from OCP.Bnd import Bnd_Box
            from OCP.BRepBndLib import BRepBndLib
            from OCP.STEPControl import STEPControl_Reader

            reader = STEPControl_Reader()
            reader.ReadFile(str(step))
            reader.TransferRoots()
            bounds = Bnd_Box()
            BRepBndLib.Add_s(reader.OneShape(), bounds)
            x_min, y_min, z_min, x_max, y_max, z_max = bounds.Get()
            self.assertAlmostEqual(x_min, -1.0, places=5)
            self.assertAlmostEqual(y_max, 1.0, places=5)
            self.assertAlmostEqual(z_min, 0.0, places=5)
            self.assertAlmostEqual(z_max, 0.85, places=5)


if __name__ == "__main__":
    unittest.main()
