"""KiCad adapter for architecture IR."""

from __future__ import annotations

import csv
import html
import re
import uuid
from pathlib import Path
from typing import Any


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


class EDAAdapter:
    """Implement export(ir, out_dir) for another EDA."""

    def export(self, ir: dict[str, Any], out_dir: Path) -> list[Path]:
        raise NotImplementedError


class KiCadAdapter(EDAAdapter):
    def export(self, ir: dict[str, Any], out_dir: Path) -> list[Path]:
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
