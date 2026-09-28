# Awesome Circuit Skills

Two reusable skills for the early stages of AI assisted circuit design:

| Skill | Input | Output |
| --- | --- | --- |
| [EDA Component Generator](skills/eda-component-generator/SKILL.md) | Exact part/package datasheet | Evidence-backed Component IR, KiCad symbol, footprint, and simple VRML 3D model |
| [Hardware Architecture Generator](skills/hardware-architecture-generator/SKILL.md) | System requirements and known parts | Architecture IR, block diagram, power tree, and pin resource plan |

Both skills use [versioned, EDA-independent JSON contracts](docs/ir-contracts.md). A [Python adapter interface](circuit_skills/adapters/base.py) isolates KiCad output so another EDA can be added without changing the IR. No runtime packages are required beyond Python 3.10 or newer.

## Workflow

1. Use the relevant Skill to extract facts and decisions into JSON. Include datasheet page or figure references for critical part data.
2. Run `python -m circuit_skills validate component.json` or `python -m circuit_skills validate architecture.json`.
3. Run `python -m circuit_skills export component.json --eda kicad --out output` or the same command for architecture JSON.
4. Review the generated report and inspect the artifacts in KiCad before using them in a design.

The component exporter requires explicit pad coordinates and dimensions from a recommended land pattern or documented calculation. It does not infer missing geometry from a package name. Its 3D output is a simple body and lead approximation in KiCad-compatible VRML; STEP export and complex package families are future adapter work. The architecture KiCad output is a graphical overview, not an electrically connected schematic.

`main` is the stable baseline. The two skills are developed on `develop`; this branch is intentionally kept separate from `main`.
