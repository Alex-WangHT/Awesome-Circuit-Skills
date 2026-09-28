# IR contracts, version 1

The two skills produce JSON with `schema_version: 1` and `kind: "component"` or `"architecture"`. Names and IDs are stable identifiers. Lengths are millimeters, voltage is volts, current is amperes. A `source` object points to the datasheet page, figure, table, or requirement that supports a fact. Missing engineering facts belong in `unresolved`; they must not be silently guessed.

## Component IR

See [the example](../examples/component.json). Required top-level keys: `identity`, `package`, `pins`, `footprint`, `model3d`, and `sources`.

- `identity`: exact `manufacturer`, `part_number`, and `package_variant`.
- `package`: `pin_count` and body width, length, height in millimeters.
- `pins`: unique physical `number`, `name`, KiCad-compatible electrical `type`, `unit`, and `source`. Include NC and exposed pads if they are physical contacts. Multi-unit grouping is represented by `unit`.
- `footprint.pads`: unique `number`, center `x_mm`/`y_mm`, `width_mm`/`height_mm`, and `shape` (`rect`, `roundrect`, `circle`, or `oval`). Coordinates are relative to the package center; positive Y points down on the PCB. `footprint.source` identifies a recommended land pattern or a documented calculation.
- `footprint.courtyard`: width and length in millimeters. `footprint.pin1_at` names the pin-1 pad so the renderer can place its marker nearby.
- `model3d`: `body_standoff_mm` and `lead_thickness_mm`. The exported VRML model has the package dimensions and pad-aligned lead approximation.
- `sources`: `datasheet` and `revision` for traceability. A local path or URL may be used for `datasheet`.

Validation checks identity, source references, counts, unique pin and pad numbers, one-to-one pin/pad numbering, finite positive geometry, pad placement within the courtyard, pin 1 orientation, and package dimensions. These are structural checks; they cannot prove that extracted facts match the datasheet. A reviewer must compare the verification report and exported files against the source drawing.

## Architecture IR

See [the example](../examples/architecture.json). Required top-level keys: `metadata`, `requirements`, `blocks`, `interfaces`, `power_tree`, `clock_tree`, `reset_tree`, `pinmap`, and `unresolved`.

- `requirements`: each has unique `id`, `text`, `priority` (`required`, `preferred`, `optional`, or `unknown`) and `source`.
- `blocks`: each has unique `id`, `type`, `implements` requirement IDs, and optional `component_ref`. `needs_power`, `needs_clock`, and `needs_reset` indicate design needs explicitly.
- `interfaces`: each has unique `id`, `from`, `to`, `type`, and `signals`. Optional `voltage_v`, `timing`, and `constraints` keep the interface contract together.
- `power_tree.inputs`: external rails with `id`, `voltage_v`, and `source`.
- `power_tree.rails`: each has `id`, `voltage_v`, `source` (input or rail ID), `loads` (block IDs), and optional current, tolerance, noise, and sequencing data. A rail graph must have no cycles.
- `clock_tree` and `reset_tree`: sources and consumers are block IDs or named external sources, with known frequency, polarity, and timing when available.
- `pinmap`: logical controller resource assignments. Each has `controller`, `resource`, `interface`, `status` (`proposed` or `confirmed`), and optional `io_bank`, `io_voltage_v`, `physical_pin`, and `source`. A confirmed physical pin requires a source. Resource and physical pin assignments must be unique; an explicit IO voltage must match its interface contract.
- `unresolved`: explicit questions or missing data. The validator also reports missing requirement coverage, missing power/clock/reset sources, unknown endpoints, and conflicting resource assignments.

The architecture exporter writes Mermaid diagrams, a pin map CSV, a validation report, and a **graphical** KiCad overview. The overview deliberately contains no electrical wires, labels, or pin assignments; it cannot be used as a finished circuit schematic. This keeps visual architecture separate from verified electrical connectivity.

## Adapter boundary

`EDAAdapter.export_component(ir, out_dir)` and `EDAAdapter.export_architecture(ir, out_dir)` receive the validated IR and write EDA-specific files. The common validator, skill instructions, and IR do not import KiCad internals. The `--eda` registry currently exposes `kicad`; another adapter may implement the same interface for LCEDA or another tool.
