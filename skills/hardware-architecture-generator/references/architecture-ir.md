# Architecture IR (version 1)

The architecture Skill writes JSON with `schema_version: 1` and `kind: "architecture"`. The [synthetic example](architecture.json) shows the fields. Use stable IDs; voltage is volts and current is amperes. Place unknown engineering facts in `unresolved` rather than guessing.

- `requirements`: each has unique `id`, `text`, `priority` (`required`, `preferred`, `optional`, or `unknown`) and `source`.
- `blocks`: each has unique `id`, `type`, `implements` requirement IDs, and optional `component_ref`. `needs_power`, `needs_clock`, and `needs_reset` express explicit design needs.
- `interfaces`: each has unique `id`, `from`, `to`, `type`, and `signals`. Optional `voltage_v`, `timing`, and `constraints` keep the contract together.
- `power_tree.inputs`: external supplies with `id`, `voltage_v`, and `source`.
- `power_tree.rails`: `id`, `voltage_v`, `source` (input or rail ID), `loads` (block IDs), and optional current, tolerance, noise, and sequencing data. The rail graph must be acyclic.
- `clock_tree` and `reset_tree`: named sources and block consumers, with frequency, polarity, and timing when known.
- `pinmap`: logical controller assignments with `controller`, `resource`, `interface`, `status` (`proposed` or `confirmed`), and optional `io_bank`, `io_voltage_v`, `physical_pin`, and `source`. Confirmed physical pins require a datasheet source. Resources and physical pins must be unique; an explicit IO voltage must match its interface.
- `unresolved`: missing data and decisions still open.

The validator reports uncovered required functions, unknown endpoints, missing power/clock/reset sources, cycles, and resource conflicts. The adapter writes Mermaid diagrams, a pin map CSV, a validation report, and a **graphical** KiCad overview. The overview contains no electrical wires or assigned symbol pins and is not a complete circuit schematic.
