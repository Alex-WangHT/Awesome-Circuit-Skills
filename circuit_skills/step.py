"""Create a real STEP compound from explicit package dimensions and pad geometry."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def export_step(ir: dict[str, Any], path: Path) -> Path:
    try:
        from OCP.BRep import BRep_Builder
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.STEPControl import STEPControl_AsIs, STEPControl_Reader, STEPControl_Writer
        from OCP.TopoDS import TopoDS_Compound
        from OCP.gp import gp_Pnt
    except ImportError as exc:
        raise RuntimeError(
            "STEP export requires cadquery-ocp and its VTK runtime; install skills/eda-component-generator/requirements.txt"
        ) from exc

    def box(x: float, y: float, z: float, width: float, length: float, height: float):
        # KiCad footprint Y is down; the STEP model uses a right-handed Y-up frame.
        return BRepPrimAPI_MakeBox(
            gp_Pnt(x - width / 2, -y - length / 2, z),
            gp_Pnt(x + width / 2, -y + length / 2, z + height),
        ).Shape()

    body = ir["package"]["body"]
    model = ir["model3d"]
    compound = TopoDS_Compound()
    builder = BRep_Builder()
    builder.MakeCompound(compound)
    builder.Add(
        compound,
        box(0, 0, model["body_standoff_mm"], body["width_mm"], body["length_mm"], body["height_mm"]),
    )
    for pad in ir["footprint"]["pads"]:
        builder.Add(
            compound,
            box(pad["x_mm"], pad["y_mm"], 0, pad["width_mm"], pad["height_mm"], model["lead_thickness_mm"]),
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    writer = STEPControl_Writer()
    writer.Transfer(compound, STEPControl_AsIs)
    if writer.Write(str(path)) != IFSelect_RetDone:
        raise RuntimeError("OpenCascade failed to write the STEP model")
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_RetDone or reader.TransferRoots() < 1:
        raise RuntimeError("The generated STEP model failed an OpenCascade round-trip check")
    if reader.OneShape().IsNull():
        raise RuntimeError("The generated STEP model contains no geometry")
    return path
