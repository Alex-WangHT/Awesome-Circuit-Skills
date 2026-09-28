# Component IR (version 1)

The component Skill writes JSON with `schema_version: 1` and `kind: "component"`. The [synthetic example](component.json) shows every required key. Lengths are millimeters. A `source` names the datasheet page, figure, table, or published calculation behind a fact. Missing critical information belongs in `unresolved` and blocks formal export.

- `identity`: exact `manufacturer`, `part_number`, and `package_variant`.
- `package`: `pin_count`, body width, length, height, and a mechanical drawing source.
- `pins`: unique physical `number`, `name`, electrical `type`, functional `unit`, and pin-table `source`. Include NC, reserved, and exposed-pad contacts when present.
- `footprint.pads`: unique `number`, center `x_mm`/`y_mm`, `width_mm`/`height_mm`, and `shape` (`rect`, `roundrect`, `circle`, or `oval`). Coordinates are relative to the package center; positive Y points down on the PCB. `footprint.source` identifies the recommended land pattern or documented calculation.
- `footprint.courtyard`: width and length. `footprint.pin1_at` identifies the pin-1 pad for its marker.
- `model3d`: `body_standoff_mm` and `lead_thickness_mm`. The exported STEP model contains a solid package body and pad-aligned lead solids at the footprint origin. It is an envelope approximation; do not infer hidden internal geometry.
- `sources`: `datasheet` location and `revision`.

The validator checks identity, references, counts, unique pin and pad numbers, one-to-one numbering, finite positive geometry, overlapping pads, courtyard containment, and pin-1 identification. Structural consistency cannot prove that extracted facts match the datasheet. Compare exported files with the source drawing before design use.
