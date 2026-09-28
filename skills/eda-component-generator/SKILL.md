---
name: eda-component-generator
description: Generate a datasheet-backed EDA symbol, PCB footprint, and 3D model for one exact component and package variant. Use when a user provides a datasheet or part package to build library assets; do not use to design circuit connections.
---

# EDA Component Generator

Turn one exact manufacturer part and package variant into [Component IR](references/component-ir.md), then use the deterministic adapter to export EDA library files. The input can be a PDF, a manufacturer page, or a package drawing; obtain the original source before asserting dimensions or pin assignments.

1. Identify manufacturer, full orderable part number, package code and variant, pin count, datasheet revision, and the pages or figures used. Keep package variants separate. If identity or package is ambiguous, record it in `unresolved` and request the missing choice.
2. Extract every physical contact, including NC, reserved, and exposed pad contacts. Preserve exact pin numbers and names. Map electrical types conservatively and group a large symbol into functional `unit` values. Record a source for the pin table.
3. Extract the package drawing and recommended land pattern. Enter explicit pad coordinates and sizes in millimeters. If deriving pads from a published standard or application note, record the method and its source. Never invent missing critical dimensions.
4. Fill `package`, `footprint`, and `model3d` in Component IR. The 3D model is mechanical; prioritize envelope, height, origin, and pin-1 orientation. See [IR contract](references/component-ir.md) and [example](references/component.json).
5. From the repository root, run `python -m circuit_skills validate path/to/component.json`. Resolve all failures before export. Install [STEP requirements](requirements.txt) if needed. Run `python -m circuit_skills export path/to/component.json --eda kicad --out output-dir` to produce `.kicad_sym`, `.kicad_mod`, and `.step` plus a verification report.
6. Open the result in KiCad when available. Compare symbol numbers to datasheet pins, footprint pad dimensions and pitch to the land pattern, and 3D body position to the mechanical drawing. Report unverified visual inspection if KiCad is unavailable.

Stop formal export if the package cannot be identified, contacts disagree, pin assignment is incomplete, or critical mechanical or land-pattern dimensions are missing. Provide the partial IR and a concise `requires_review` report listing the exact missing evidence. The validator checks consistency within the IR; it cannot certify source extraction or manufacturability.

The first adapter supports explicit SMD pad geometry and a STEP body/lead model. It does not derive land patterns or represent complex molded features. For unsupported geometry, preserve the IR and state the adapter limitation rather than writing a plausible-looking substitute.
