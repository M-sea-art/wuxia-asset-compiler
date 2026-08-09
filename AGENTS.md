# AGENTS.md

## Project identity

Wuxia Asset Compiler is a code-native, template-driven 3D asset pipeline for original stylized wuxia game worlds.

The production path is:

`reference -> scene spec -> factory/style DNA -> Blender -> validation -> GLB -> engine`

## Core rules

- Prefer deterministic factories, Geometry Nodes, typed tools, and bounded parameters over ad-hoc generated `bpy`.
- The LLM/VLM interprets intent and references; deterministic code owns geometry truth, measurements, validation, and export readiness.
- Keep the public agent action surface small. Prefer task-level macros/workflows over exposing every low-level Blender operation.
- Scene specs are versioned contracts. Do not silently change parameter meanings.
- Factories must be reproducible for the same spec + seed.
- New variation belongs in explicit parameters, style DNA, modules, or seeded rules.
- Do not copy protected characters, faction marks, named locations, or distinctive visual designs from existing martial-arts IP.
- Do not copy code from third-party repositories unless its license is explicitly compatible and attribution/notice obligations are recorded.
- Generated assets intended for games must be validated before export.

## Validation priorities

Before considering an asset production-ready, validate at least:

- dimensions and scale
- transforms and pivot/origin
- mesh count and polygon budget
- degenerate/non-manifold geometry where relevant
- normals
- material slots and texture references
- UV presence where required
- collision strategy
- GLB export success
- engine import success

Vision-based comparison may suggest repairs, but it is not the final truth layer for geometric correctness.

## Change discipline

- Keep factories modular and readable.
- Avoid giant one-off scripts.
- Add a small example spec and a deterministic smoke test for every new factory family.
- Prefer parameter patches over regenerating an entire asset during iterative visual repair.
