---
name: hardware-architecture-generator
description: Convert hardware requirements into a block diagram, power tree, interfaces, and logical pin resource plan. Use for system architecture before detailed schematic design; do not treat its outputs as verified electrical connections.
---

# Hardware Architecture Generator

Convert the user's requirements into [Architecture IR](../../docs/ir-contracts.md), then derive diagrams and pin planning artifacts from that single source. Use known component datasheets or existing Component IR when deciding device-specific voltage, clock, reset, or pin capabilities.

1. Capture each requirement with a stable ID, priority, and source. Keep unknown targets and tradeoffs in `unresolved`; state assumptions in the output.
2. Create functional blocks and link each requirement to the blocks that implement it. Connect blocks with typed interface contracts: endpoints, signal groups, direction, voltage, timing, and constraints when known. Do not reduce an interface to isolated pin-to-pin claims at this stage.
3. Build a power graph from input supplies through rails to block loads. Add voltage, estimated current, tolerance, noise, and sequencing where supported. Then define clock and reset sources, consumers, polarity, and timing.
4. Plan controller resources logically: peripheral instance, IO bank or voltage domain, dedicated pins, clock capable pins, differential pairs, boot/debug reservations. Use `proposed` when physical pins are not confirmed. A `confirmed` physical assignment needs a datasheet source. See [IR contract](../../docs/ir-contracts.md) and [example](../../examples/architecture.json).
5. Run `python -m circuit_skills validate path/to/architecture.json`. Resolve structural errors and review warnings. Export with `python -m circuit_skills export path/to/architecture.json --eda kicad --out output-dir` to create block and power diagrams, pinmap CSV, report, and a graphical KiCad overview.

Check that every required function has a block, each endpoint exists, every powered IC has a rail, clock and reset consumers have sources, voltages are compatible when known, and controller resources are not assigned twice. Report open issues as such. The KiCad overview is an architecture drawing and must not be promoted to a complete schematic or netlist.
