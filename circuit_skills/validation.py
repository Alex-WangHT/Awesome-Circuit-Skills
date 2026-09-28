"""Structural validation for the versioned component and architecture IR."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any


PIN_TYPES = {
    "input", "output", "bidirectional", "tri_state", "passive", "free",
    "unspecified", "power_in", "power_out", "open_collector",
    "open_emitter", "no_connect",
}
PAD_SHAPES = {"rect", "roundrect", "circle", "oval"}


def validate(ir: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []

    def add(level: str, code: str, path: str, message: str) -> None:
        issues.append({"level": level, "code": code, "path": path, "message": message})

    if not isinstance(ir, dict):
        add("error", "root_type", "root", "IR root must be a JSON object")
        return {"status": "FAIL", "issues": issues}
    if ir.get("schema_version") != 1:
        add("error", "schema_version", "schema_version", "Expected schema version 1")
    kind = ir.get("kind")
    try:
        if kind == "component":
            _component(ir, add)
        elif kind == "architecture":
            _architecture(ir, add)
        else:
            add("error", "kind", "kind", "Expected component or architecture")
    except (AttributeError, TypeError, ValueError, KeyError) as exc:
        add("error", "malformed_ir", "root", f"Malformed IR structure: {exc}")
    status = "FAIL" if any(i["level"] == "error" for i in issues) else (
        "REQUIRES_REVIEW" if issues else "PASS"
    )
    return {"status": status, "issues": issues}


def _required_text(value: Any, path: str, add) -> None:
    if not isinstance(value, str) or not value.strip():
        add("error", "required_text", path, "A nonempty string is required")


def _positive(value: Any, path: str, add, allow_zero: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (
        value < 0 if allow_zero else value <= 0
    ):
        add("error", "positive_number", path, "Expected a finite nonnegative number" if allow_zero else "Expected a finite positive number")


def _unique(values: list[Any], path: str, add) -> None:
    for item, count in Counter(values).items():
        if count > 1:
            add("error", "duplicate_id", path, f"Duplicate value: {item}")


def _component(ir: dict[str, Any], add) -> None:
    identity = ir.get("identity") or {}
    for key in ("manufacturer", "part_number", "package_variant"):
        _required_text(identity.get(key), f"identity.{key}", add)
    sources = ir.get("sources") or {}
    for key in ("datasheet", "revision"):
        _required_text(sources.get(key), f"sources.{key}", add)
    package = ir.get("package") or {}
    pin_count = package.get("pin_count")
    if not isinstance(pin_count, int) or isinstance(pin_count, bool) or pin_count < 1:
        add("error", "pin_count", "package.pin_count", "Expected a positive integer")
    body = package.get("body") or {}
    for key in ("width_mm", "length_mm", "height_mm"):
        _positive(body.get(key), f"package.body.{key}", add)
    _required_text(package.get("source"), "package.source", add)

    pins = ir.get("pins") or []
    pads = (ir.get("footprint") or {}).get("pads") or []
    if not isinstance(pins, list) or not pins:
        add("error", "pins_missing", "pins", "At least one pin is required")
        pins = []
    if not isinstance(pads, list) or not pads:
        add("error", "pads_missing", "footprint.pads", "At least one pad is required")
        pads = []
    pin_numbers = [str(p.get("number", "")) for p in pins if isinstance(p, dict)]
    pad_numbers = [str(p.get("number", "")) for p in pads if isinstance(p, dict)]
    _unique(pin_numbers, "pins", add)
    _unique(pad_numbers, "footprint.pads", add)
    if isinstance(pin_count, int) and (len(pins) != pin_count or len(pads) != pin_count):
        add("error", "pin_count_mismatch", "package.pin_count", "Package, symbol pin, and footprint pad counts differ")
    if set(pin_numbers) != set(pad_numbers):
        add("error", "pin_pad_mismatch", "footprint.pads", "Pin and pad numbers do not match one-to-one")
    for n, pin in enumerate(pins):
        if not isinstance(pin, dict):
            add("error", "pin_record", f"pins[{n}]", "Expected an object")
            continue
        for key in ("number", "name", "unit", "source"):
            _required_text(pin.get(key), f"pins[{n}].{key}", add)
        if pin.get("type") not in PIN_TYPES:
            add("error", "pin_type", f"pins[{n}].type", "Unsupported electrical pin type")

    footprint = ir.get("footprint") or {}
    for key in ("name", "source", "pin1_at"):
        _required_text(footprint.get(key), f"footprint.{key}", add)
    if footprint.get("pin1_at") not in pad_numbers:
        add("error", "pin1_missing", "footprint.pin1_at", "Pin 1 marker must identify a pad")
    courtyard = footprint.get("courtyard") or {}
    for key in ("width_mm", "length_mm"):
        _positive(courtyard.get(key), f"footprint.courtyard.{key}", add)
    for n, pad in enumerate(pads):
        if not isinstance(pad, dict):
            add("error", "pad_record", f"footprint.pads[{n}]", "Expected an object")
            continue
        _required_text(pad.get("number"), f"footprint.pads[{n}].number", add)
        if pad.get("shape") not in PAD_SHAPES:
            add("error", "pad_shape", f"footprint.pads[{n}].shape", "Unsupported pad shape")
        for key in ("x_mm", "y_mm"):
            value = pad.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                add("error", "coordinate", f"footprint.pads[{n}].{key}", "Expected a finite coordinate")
        for key in ("width_mm", "height_mm"):
            _positive(pad.get(key), f"footprint.pads[{n}].{key}", add)
        if all(isinstance(pad.get(k), (int, float)) for k in ("x_mm", "y_mm", "width_mm", "height_mm")) and all(isinstance(courtyard.get(k), (int, float)) for k in ("width_mm", "length_mm")):
            if abs(pad["x_mm"]) + pad["width_mm"] / 2 > courtyard["width_mm"] / 2 or abs(pad["y_mm"]) + pad["height_mm"] / 2 > courtyard["length_mm"] / 2:
                add("error", "pad_outside_courtyard", f"footprint.pads[{n}]", "Pad extends outside courtyard")
    for n, first in enumerate(pads):
        if not isinstance(first, dict) or not all(isinstance(first.get(k), (int, float)) for k in ("x_mm", "y_mm", "width_mm", "height_mm")):
            continue
        for m in range(n + 1, len(pads)):
            second = pads[m]
            if not isinstance(second, dict) or not all(isinstance(second.get(k), (int, float)) for k in ("x_mm", "y_mm", "width_mm", "height_mm")):
                continue
            if abs(first["x_mm"] - second["x_mm"]) < (first["width_mm"] + second["width_mm"]) / 2 and abs(first["y_mm"] - second["y_mm"]) < (first["height_mm"] + second["height_mm"]) / 2:
                add("error", "pad_overlap", f"footprint.pads[{n}]", f"Pad overlaps footprint.pads[{m}]")
    model = ir.get("model3d") or {}
    for key in ("body_standoff_mm", "lead_thickness_mm"):
        _positive(model.get(key), f"model3d.{key}", add, allow_zero=key == "body_standoff_mm")
    if ir.get("unresolved"):
        add("error", "unresolved", "unresolved", "Resolve critical missing facts before formal export")


def _architecture(ir: dict[str, Any], add) -> None:
    metadata = ir.get("metadata") or {}
    _required_text(metadata.get("name"), "metadata.name", add)
    requirements = ir.get("requirements") or []
    blocks = ir.get("blocks") or []
    interfaces = ir.get("interfaces") or []
    if not isinstance(requirements, list) or not isinstance(blocks, list) or not isinstance(interfaces, list):
        add("error", "collections", "architecture", "Requirements, blocks, and interfaces must be lists")
        return
    for collection, name in ((requirements, "requirements"), (blocks, "blocks"), (interfaces, "interfaces")):
        _unique([item.get("id") for item in collection if isinstance(item, dict)], name, add)
    requirement_ids = {r.get("id") for r in requirements if isinstance(r, dict)}
    block_ids = {b.get("id") for b in blocks if isinstance(b, dict)}
    interface_ids = {i.get("id") for i in interfaces if isinstance(i, dict)}
    for n, r in enumerate(requirements):
        for key in ("id", "text", "source"):
            _required_text(r.get(key), f"requirements[{n}].{key}", add)
        if r.get("priority") not in {"required", "preferred", "optional", "unknown"}:
            add("error", "priority", f"requirements[{n}].priority", "Invalid requirement priority")
    for n, b in enumerate(blocks):
        for key in ("id", "type"):
            _required_text(b.get(key), f"blocks[{n}].{key}", add)
        for requirement in b.get("implements", []):
            if requirement not in requirement_ids:
                add("error", "unknown_requirement", f"blocks[{n}].implements", f"Unknown requirement: {requirement}")
    covered = {r for b in blocks for r in b.get("implements", [])}
    for r in requirements:
        if r.get("priority") == "required" and r.get("id") not in covered:
            add("warning", "requirement_uncovered", "requirements", f"Required function {r.get('id')} has no block")
    for n, interface in enumerate(interfaces):
        for key in ("id", "type"):
            _required_text(interface.get(key), f"interfaces[{n}].{key}", add)
        for endpoint in ("from", "to"):
            if interface.get(endpoint) not in block_ids:
                add("error", "unknown_block", f"interfaces[{n}].{endpoint}", "Interface endpoint is not a block")
        if not interface.get("signals"):
            add("warning", "signals_missing", f"interfaces[{n}].signals", "Signal group is unspecified")
        if "voltage_v" in interface:
            _positive(interface["voltage_v"], f"interfaces[{n}].voltage_v", add)
    power = ir.get("power_tree") or {}
    inputs = power.get("inputs") or []
    rails = power.get("rails") or []
    input_ids = {x.get("id") for x in inputs}
    rail_ids = {x.get("id") for x in rails}
    _unique([x.get("id") for x in inputs + rails], "power_tree", add)
    for n, inp in enumerate(inputs):
        _required_text(inp.get("id"), f"power_tree.inputs[{n}].id", add)
        _required_text(inp.get("source"), f"power_tree.inputs[{n}].source", add)
        _positive(inp.get("voltage_v"), f"power_tree.inputs[{n}].voltage_v", add)
    rail_sources = {}
    for n, rail in enumerate(rails):
        _required_text(rail.get("id"), f"power_tree.rails[{n}].id", add)
        _positive(rail.get("voltage_v"), f"power_tree.rails[{n}].voltage_v", add)
        source = rail.get("source")
        rail_sources[rail.get("id")] = source
        if source not in input_ids | rail_ids:
            add("error", "unknown_power_source", f"power_tree.rails[{n}].source", "Rail source is unknown")
        for load in rail.get("loads", []):
            if load not in block_ids:
                add("error", "unknown_load", f"power_tree.rails[{n}].loads", f"Unknown block: {load}")
    for rail_id in rail_ids:
        seen = set()
        node = rail_id
        while node in rail_sources:
            if node in seen:
                add("error", "power_cycle", "power_tree.rails", f"Cycle involving {node}")
                break
            seen.add(node)
            node = rail_sources[node]
    powered = {load for rail in rails for load in rail.get("loads", [])}
    for b in blocks:
        if b.get("needs_power") and b.get("id") not in powered:
            add("warning", "unpowered_block", "blocks", f"{b.get('id')} needs power but has no rail")
    for tree_key, need_key in (("clock_tree", "needs_clock"), ("reset_tree", "needs_reset")):
        tree = ir.get(tree_key) or []
        consumers = set()
        for n, branch in enumerate(tree):
            _required_text(branch.get("id"), f"{tree_key}[{n}].id", add)
            _required_text(branch.get("source"), f"{tree_key}[{n}].source", add)
            consumers.update(branch.get("consumers", []))
            for consumer in branch.get("consumers", []):
                if consumer not in block_ids:
                    add("error", "unknown_consumer", f"{tree_key}[{n}].consumers", f"Unknown block: {consumer}")
        for b in blocks:
            if b.get(need_key) and b.get("id") not in consumers:
                add("warning", f"missing_{tree_key}", "blocks", f"{b.get('id')} has no {tree_key} source")
    assignments = ir.get("pinmap") or []
    _unique([(p.get("controller"), p.get("resource")) for p in assignments], "pinmap", add)
    _unique([(p.get("controller"), p.get("physical_pin")) for p in assignments if p.get("physical_pin")], "pinmap.physical_pin", add)
    interface_by_id = {interface.get("id"): interface for interface in interfaces}
    for n, p in enumerate(assignments):
        if p.get("controller") not in block_ids:
            add("error", "unknown_controller", f"pinmap[{n}].controller", "Controller block is unknown")
        if p.get("interface") not in interface_ids:
            add("error", "unknown_interface", f"pinmap[{n}].interface", "Interface is unknown")
        if p.get("status") not in {"proposed", "confirmed"}:
            add("error", "pinmap_status", f"pinmap[{n}].status", "Expected proposed or confirmed")
        if p.get("status") == "confirmed" and p.get("physical_pin") and not p.get("source"):
            add("error", "pin_source_missing", f"pinmap[{n}].source", "Confirmed physical pin requires datasheet source")
        if "io_voltage_v" in p:
            _positive(p["io_voltage_v"], f"pinmap[{n}].io_voltage_v", add)
            contract = interface_by_id.get(p.get("interface")) or {}
            if isinstance(p["io_voltage_v"], (int, float)) and isinstance(contract.get("voltage_v"), (int, float)) and abs(p["io_voltage_v"] - contract["voltage_v"]) > 0.05:
                add("error", "io_voltage_conflict", f"pinmap[{n}].io_voltage_v", "Assigned IO bank voltage conflicts with interface contract")
    if ir.get("unresolved"):
        add("warning", "unresolved", "unresolved", "Open architecture decisions remain")
