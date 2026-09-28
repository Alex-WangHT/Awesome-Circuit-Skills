"""Deterministic KiCad exporter for explicit Component and Architecture IR."""

from __future__ import annotations

import csv
import html
import re
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from .base import EDAAdapter


def _q(value: Any) -> str:
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def _f(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def _slug(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_.+-]+", "_", value).strip("_")
    if not result:
        raise ValueError("A part or project name must contain letters or digits")
    return result


def _uid(namespace: str, item: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"awesome-circuit-skills:{namespace}:{item}"))


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _symbol_property(key: str, value: str, y: float, hidden: bool = False) -> str:
    return f'    (property {_q(key)} {_q(value)} (at 0 {_f(y)} 0) (effects (font (size 1.27 1.27))' + (' (hide yes)' if hidden else '') + '))'


def _symbol(ir: dict[str, Any], name: str) -> str:
    units: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pin in ir["pins"]:
        units[pin["unit"]].append(pin)
    lines = [
        '(kicad_symbol_lib (version 20231120) (generator awesome_circuit_skills)',
        f'  (symbol {_q(name)} (pin_names (offset 0.508)) (in_bom yes) (on_board yes)',
        _symbol_property("Reference", "U", 7.62),
        _symbol_property("Value", name, 5.08),
        _symbol_property("Footprint", f"AwesomeCircuit:{name}", 0, True),
        _symbol_property("Datasheet", ir["sources"]["datasheet"], -2.54, True),
    ]
    for index, (unit, pins) in enumerate(units.items(), 1):
        left = [p for p in pins if p["type"] not in {"output", "power_out"}]
        right = [p for p in pins if p["type"] in {"output", "power_out"}]
        row_count = max(len(left), len(right), 1)
        half_w = 12.7
        half_h = max(7.62, (row_count + 1) * 1.27)
        lines.append(f'    (symbol {_q(f"{name}_{index}_1")} (unit_name {_q(unit)})')
        lines.append(f'      (rectangle (start {-half_w} {_f(half_h)}) (end {half_w} {_f(-half_h)}) (stroke (width 0.254) (type default)) (fill (type background)))')
        for side, side_pins in (("left", left), ("right", right)):
            for row, pin in enumerate(side_pins):
                y = (len(side_pins) - 1) * 1.27 - row * 2.54
                x = -half_w - 2.54 if side == "left" else half_w + 2.54
                angle = 0 if side == "left" else 180
                lines.append(
                    f'      (pin {pin["type"]} line (at {_f(x)} {_f(y)} {angle}) (length 2.54) '
                    f'(name {_q(pin["name"])} (effects (font (size 1.27 1.27)))) '
                    f'(number {_q(pin["number"])} (effects (font (size 1.27 1.27)))))'
                )
        lines.append('    )')
    lines += ['  )', ')', '']
    return '\n'.join(lines)


def _footprint(ir: dict[str, Any], name: str) -> str:
    footprint = ir["footprint"]
    body = ir["package"]["body"]
    court = footprint["courtyard"]
    lines = [
        f'(footprint {_q(name)} (version 20221018) (generator awesome_circuit_skills)',
        '  (layer "F.Cu")',
        f'  (descr {_q(ir["identity"]["manufacturer"] + " " + ir["identity"]["part_number"] + "; " + ir["identity"]["package_variant"])})',
        '  (attr smd)',
        f'  (fp_text reference "REF**" (at 0 {_f(-court["length_mm"] / 2 - 1.5)}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
        '  (fp_text value ' + _q(name) + ' (at 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
        f'  (fp_rect (start {_f(-body["width_mm"]/2)} {_f(-body["length_mm"]/2)}) (end {_f(body["width_mm"]/2)} {_f(body["length_mm"]/2)}) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',
        f'  (fp_rect (start {_f(-court["width_mm"]/2)} {_f(-court["length_mm"]/2)}) (end {_f(court["width_mm"]/2)} {_f(court["length_mm"]/2)}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
    ]
    pin1 = next(p for p in footprint["pads"] if str(p["number"]) == str(footprint["pin1_at"]))
    mark_x = max(-court["width_mm"] / 2 + 0.3, min(court["width_mm"] / 2 - 0.3, pin1["x_mm"] + (-0.4 if pin1["x_mm"] <= 0 else 0.4)))
    mark_y = max(-court["length_mm"] / 2 + 0.3, min(court["length_mm"] / 2 - 0.3, pin1["y_mm"] + (-0.4 if pin1["y_mm"] <= 0 else 0.4)))
    lines.append(f'  (fp_circle (center {_f(mark_x)} {_f(mark_y)}) (end {_f(mark_x + 0.25)} {_f(mark_y)}) (stroke (width 0.12) (type default)) (fill none) (layer "F.SilkS"))')
    for pad in footprint["pads"]:
        rratio = ' (roundrect_rratio 0.15)' if pad["shape"] == "roundrect" else ''
        lines.append(
            f'  (pad {_q(pad["number"])} smd {pad["shape"]} (at {_f(pad["x_mm"])} {_f(pad["y_mm"])}) '
            f'(size {_f(pad["width_mm"])} {_f(pad["height_mm"])}) (layers "F.Cu" "F.Paste" "F.Mask"){rratio})'
        )
    model_path = '${KIPRJMOD}/AwesomeCircuit.3dshapes/' + name + '.wrl'
    lines.append(f'  (model {_q(model_path)} (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    lines += [')', '']
    return '\n'.join(lines)


def _vrml_box(x: float, y: float, z: float, w: float, l: float, h: float, color: str) -> str:
    # KiCad's standard VRML 3D model unit is 0.1 inch = 2.54 mm.
    scale = 1 / 2.54
    return (
        f'  Transform {{ translation {_f(x*scale)} {_f(-y*scale)} {_f(z*scale)} children [ '
        f'Shape {{ appearance Appearance {{ material Material {{ diffuseColor {color} }} }} '
        f'geometry Box {{ size {_f(w*scale)} {_f(l*scale)} {_f(h*scale)} }} }} ] }}'
    )


def _model3d(ir: dict[str, Any]) -> str:
    body = ir["package"]["body"]
    model = ir["model3d"]
    height = body["height_mm"]
    standoff = model["body_standoff_mm"]
    lead_h = model["lead_thickness_mm"]
    lines = ["#VRML V2.0 utf8", "Group { children ["]
    lines.append(_vrml_box(0, 0, standoff + height / 2, body["width_mm"], body["length_mm"], height, "0.12 0.12 0.13"))
    for pad in ir["footprint"]["pads"]:
        lines.append(_vrml_box(pad["x_mm"], pad["y_mm"], lead_h / 2, pad["width_mm"], pad["height_mm"], lead_h, "0.72 0.72 0.76"))
    lines.extend(["] }", ""])
    return '\n'.join(lines)


def _mermaid_text(value: str) -> str:
    return html.escape(str(value), quote=True).replace("|", "&#124;").replace("\n", " ")


def _block_diagram(ir: dict[str, Any]) -> str:
    lines = ["flowchart LR"]
    block_ids = {block["id"]: f"B{index}" for index, block in enumerate(ir["blocks"])}
    for block in ir["blocks"]:
        label = _mermaid_text(block["id"] + ": " + block["type"])
        lines.append(f'  {block_ids[block["id"]]}["{label}"]')
    for interface in ir["interfaces"]:
        label = _mermaid_text(interface["id"] + ": " + interface["type"])
        lines.append(f'  {block_ids[interface["from"]]} -->|"{label}"| {block_ids[interface["to"]]}')
    return '\n'.join(lines) + '\n'


def _power_diagram(ir: dict[str, Any]) -> str:
    power = ir["power_tree"]
    lines = ["flowchart TD"]
    node_ids = {item["id"]: f"P{index}" for index, item in enumerate(power["inputs"] + power["rails"])}
    for inp in power["inputs"]:
        lines.append(f'  {node_ids[inp["id"]]}["{_mermaid_text(inp["id"])} {inp["voltage_v"]} V"]')
    for rail in power["rails"]:
        lines.append(f'  {node_ids[rail["id"]]}["{_mermaid_text(rail["id"])} {rail["voltage_v"]} V"]')
        lines.append(f'  {node_ids[rail["source"]]} --> {node_ids[rail["id"]]}')
        for index, load in enumerate(rail.get("loads", [])):
            load_id = f'L{len(lines)}_{index}'
            lines.append(f'  {node_ids[rail["id"]]} --> {load_id}["{_mermaid_text(load)}"]')
    return '\n'.join(lines) + '\n'


def _overview_schematic(ir: dict[str, Any]) -> str:
    """A KiCad schematic document containing graphical items only, never nets."""
    name = _slug(ir["metadata"]["name"])
    root_uuid = _uid(name, "root")
    lines = [
        '(kicad_sch (version 20231120) (generator awesome_circuit_skills)',
        f'  (uuid {root_uuid})',
        '  (paper "A3")',
        f'  (title_block (title {_q(ir["metadata"]["name"] + " - architecture overview")}))',
        '  (lib_symbols)',
    ]
    positions = {}
    for index, block in enumerate(ir["blocks"]):
        x = 30 + (index % 4) * 80
        y = 35 + (index // 4) * 55
        positions[block["id"]] = (x, y)
        points = [(x, y), (x+48, y), (x+48, y+24), (x, y+24), (x, y)]
        pts = ' '.join(f'(xy {_f(px)} {_f(py)})' for px, py in points)
        lines.append(f'  (polyline (pts {pts}) (stroke (width 0.254) (type default)) (uuid {_uid(name, "box:"+block["id"])}))')
        block_label = block["id"] + "\n" + block["type"]
        lines.append(f'  (text {_q(block_label)} (at {_f(x+24)} {_f(y+12)} 0) (effects (font (size 2 2))) (uuid {_uid(name, "block:"+block["id"])}))')
    # Interface contracts are written as annotations. Lines are graphical, not electrical wires.
    for index, interface in enumerate(ir["interfaces"]):
        x = 25 + (index % 3) * 110
        y = 225 + (index // 3) * 7
        interface_label = interface["from"] + " -> " + interface["to"] + " : " + interface["id"] + " (" + interface["type"] + ")"
        lines.append(f'  (text {_q(interface_label)} (at {_f(x)} {_f(y)} 0) (effects (font (size 1.5 1.5)) (justify left)) (uuid {_uid(name, "interface:"+interface["id"])}))')
    lines.extend(['  (sheet_instances (path "/" (page "1")))', ')', ''])
    return '\n'.join(lines)


class KiCadAdapter(EDAAdapter):
    def export_component(self, ir: dict[str, Any], out_dir: Path) -> list[Path]:
        name = _slug(ir["footprint"]["name"])
        paths = [
            _write(out_dir / 'AwesomeCircuit.kicad_sym', _symbol(ir, name)),
            _write(out_dir / 'AwesomeCircuit.pretty' / f'{name}.kicad_mod', _footprint(ir, name)),
            _write(out_dir / 'AwesomeCircuit.3dshapes' / f'{name}.wrl', _model3d(ir)),
            _write(out_dir / 'sym-lib-table', '(sym_lib_table (lib (name "AwesomeCircuit")(type "KiCad")(uri "${KIPRJMOD}/AwesomeCircuit.kicad_sym")(options "")(descr "")))\n'),
            _write(out_dir / 'fp-lib-table', '(fp_lib_table (lib (name "AwesomeCircuit")(type "KiCad")(uri "${KIPRJMOD}/AwesomeCircuit.pretty")(options "")(descr "")))\n'),
        ]
        return paths

    def export_architecture(self, ir: dict[str, Any], out_dir: Path) -> list[Path]:
        name = _slug(ir["metadata"]["name"])
        paths = [
            _write(out_dir / 'block-diagram.mmd', _block_diagram(ir)),
            _write(out_dir / 'power-tree.mmd', _power_diagram(ir)),
            _write(out_dir / f'{name}-overview.kicad_sch', _overview_schematic(ir)),
        ]
        pinmap = out_dir / 'pinmap.csv'
        pinmap.parent.mkdir(parents=True, exist_ok=True)
        with pinmap.open('w', newline='', encoding='utf-8-sig') as handle:
            writer = csv.DictWriter(handle, fieldnames=['controller', 'resource', 'interface', 'status', 'physical_pin', 'source'])
            writer.writeheader()
            for assignment in ir['pinmap']:
                writer.writerow({key: assignment.get(key, '') for key in writer.fieldnames})
        paths.append(pinmap)
        return paths
