# Awesome Circuit Skills

Two reusable skills for the early stages of AI assisted circuit design:

| Skill | Input | Output |
| --- | --- | --- |
| [EDA Component Generator](skills/eda-component-generator/SKILL.md) | Exact part/package datasheet | Evidence-backed Component IR, KiCad symbol, footprint, and STEP 3D model |
| [Hardware Architecture Generator](skills/hardware-architecture-generator/SKILL.md) | System requirements and known parts | Architecture IR, block diagram, power tree, and pin resource plan |

Each Skill contains its own versioned, EDA-independent JSON contract and example. A [Python adapter interface](circuit_skills/adapters/base.py) isolates KiCad output so another EDA can be added without changing the IR. Python 3.12 is tested; STEP export also needs the packages in the [component Skill requirements](skills/eda-component-generator/requirements.txt).

## Workflow

1. Use the relevant Skill to extract facts and decisions into JSON. Include datasheet page or figure references for critical part data.
2. Run `python -m circuit_skills validate component.json` or `python -m circuit_skills validate architecture.json`.
3. Install the STEP dependency with `python -m pip install -r skills/eda-component-generator/requirements.txt` before component export, then run `python -m circuit_skills export component.json --eda kicad --out output` (or the same command for architecture JSON).
4. Review the generated report and inspect the artifacts in KiCad before using them in a design.

The component exporter requires explicit pad coordinates and dimensions from a recommended land pattern or documented calculation. It does not infer missing geometry from a package name. Its STEP model is a solid body and pad-aligned lead approximation; complex molded features and package families need richer IR. The architecture KiCad output is a graphical overview, not an electrically connected schematic.

The KiCad footprint links to the STEP model with a path relative to its `.kicad_mod` file, so the generated library can be moved as one folder without changing the model reference.

`main` is the stable baseline. The two skills are developed on `develop`; this branch is intentionally kept separate from `main`.
