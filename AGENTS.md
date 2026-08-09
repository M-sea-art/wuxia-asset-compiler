# AGENTS.md

## Project identity

Wuxia Asset Compiler is a **code-native, template-driven 3D asset compiler** for original stylized wuxia and eastern-fantasy game worlds.

The project exists to convert visual intent into bounded, reproducible, game-ready 3D assets while accumulating reusable modeling capability over time.

Canonical production direction:

`reference -> reference analysis -> resolver -> scene spec -> style/factory -> Blender -> visual QA -> bounded repair or template gap -> validation -> GLB -> engine`

The important word is **compiler**. Agents interpret and propose; contracts, factories, measurements, and validators decide what becomes geometry.

See:

- `docs/PROJECT_PHILOSOPHY.zh-CN.md` for the long-form project doctrine.
- `docs/CODEX_SKILLS_PLUGIN.zh-CN.md` for the Codex Skills / Plugin integration model.

---

## Codex operating model

Codex is the preferred **engineering agent and Skill host around the compiler**. It is not the geometry truth layer.

Codex should primarily:

- read and obey this repository's `AGENTS.md`;
- invoke stable compiler CLIs, typed tools, Skills, or high-level MCP operations;
- implement reusable Macro / Factory / Style-DNA capabilities when a `template_gap` is confirmed;
- add or update tests;
- run contract tests and Blender smoke tests;
- inspect CI results;
- produce reviewable pull requests.

Codex should not treat unrestricted Blender Python as the normal solution path.

### Recommended Skill decomposition

Prefer small composable Skills such as:

- `wuxia-reference-analysis`
- `wuxia-resolve-spec`
- `wuxia-compile-asset`
- `wuxia-visual-qa`
- `wuxia-repair-asset`
- `wuxia-template-gap-engineer`
- `wuxia-asset-validator`
- `wuxia-godot-import-smoke`

A Skill describes **how to perform one repeatable workflow**. This `AGENTS.md` describes **what must always be true when working in this repository**.

Do not duplicate the entire repository doctrine into every Skill. Skills should reference the project contract and keep their task-specific instructions focused.

### Preferred Codex tool surface

Good production-facing actions:

```text
resolve_reference
compile_scene_spec
render_qa_views
apply_visual_review
validate_asset
export_glb
inspect_scene_metrics
implement_template_gap
run_godot_import_smoke
```

Avoid making these the default agent surface:

```text
move_vertex
extrude_face
run_arbitrary_bpy
execute_unbounded_python
```

Raw scripting may be used as a narrow engineering/debugging escape hatch, but repeated workflows should be promoted into a typed tool, Semantic Macro, Factory, CLI, or Skill.

### Plugin boundary

A future Wuxia Asset Compiler Codex plugin may package multiple project Skills plus optional connected capabilities such as repository access, Blender MCP, CI, or engine integration.

The plugin must not weaken existing project contracts. Installing a Skill or Plugin does not change the authority hierarchy below.

---

## Authority hierarchy

When sources of truth disagree, use this order:

1. executable compiler / schema contract;
2. deterministic geometry measurement and validation;
3. factory ownership and bounded parameter rules;
4. visual QA observations;
5. LLM/VLM/Codex suggestions;
6. free-form generated code.

A visual model may suggest that something looks correct. It does not overrule deterministic measurements.

---

## Core rules

- Prefer deterministic factories, Geometry Nodes, typed tools, semantic macros, and bounded parameters over ad-hoc generated `bpy`.
- The LLM/VLM interprets intent and references; deterministic code owns geometry truth, measurements, validation, and export readiness.
- Codex engineers and operates the compiler; it does not become a bypass around the compiler.
- Keep the public agent action surface small. Prefer task-level macros/workflows over exposing every low-level Blender operation.
- Scene specs and review objects are versioned contracts. Do not silently change parameter meanings.
- Factories must be reproducible for the same spec + seed.
- New variation belongs in explicit parameters, Style DNA, modules, macros, factories, or seeded rules.
- Every accepted visual patch must pass the complete compiler contract again.
- Do not silently clamp hallucinated or invalid model proposals when rejection is more informative. Record the decision and keep deterministic state.
- Do not copy protected characters, faction marks, named locations, or distinctive visual designs from existing martial-arts IP.
- Do not copy third-party code unless its license is explicitly compatible and attribution / notice obligations are understood and recorded.
- Generated assets intended for games must be validated before export.

---

## The template-gap rule

Visual QA must distinguish two fundamentally different failure classes.

### Parameter-fixable

Examples:

- a room is too wide;
- prop density is too low;
- lantern count is wrong;
- timber aging is wrong;
- cliff embed is wrong.

These may become bounded parameter patches.

### Capability gap

Examples:

- no tall shelf macro exists;
- no hanging herb module exists;
- no population-slot layer exists;
- no bracket / railing vocabulary exists;
- no atmospheric staging exists.

These must become a structured `template_gap` or engineering backlog item.

**Never compensate for a missing capability by driving unrelated scalar parameters to extreme values.**

A clean declaration of “the current DSL cannot express this” is a successful system behavior.

For Codex, a `template_gap` is often the correct handoff from asset-generation workflow to software-engineering workflow:

```text
template_gap
    -> identify abstraction level
    -> implement reusable capability
    -> add tests
    -> run Blender smoke
    -> review PR
```

---

## Preferred capability ladder

Grow the project upward through reusable abstractions:

```text
Primitive
  -> Semantic Macro
  -> Room / Asset Factory
  -> Compound Factory
  -> Style DNA
  -> World-scale Assembly
```

Before adding a new one-off room implementation, ask whether the underlying capability should be a reusable Macro.

Before exposing another low-level Blender function to an agent or Skill, ask whether the task can be expressed by a higher-level semantic operation.

---

## Cost and scaling principle

Do not optimize only for the quality of one render.

Prefer designs that amortize work across asset families:

- one good Macro should improve many rooms;
- one Factory should create many controlled variations;
- one Style DNA preset should keep a whole world coherent;
- one well-designed Codex Skill should make a repeatable workflow cheaper and more reliable across tasks;
- expensive image-to-3D generation may be used to bootstrap or teach templates, but should not automatically become a permanent per-asset dependency.

Token cost, GPU dependency, repeatability, maintenance cost, and downstream editing cost are production concerns, not afterthoughts.

---

## Validation priorities

Before considering an asset production-ready, validate at least:

- dimensions and scale;
- transforms and pivot/origin;
- mesh count and polygon / triangle budget;
- degenerate/non-manifold geometry where relevant;
- normals;
- material slots and texture references;
- UV presence where required;
- collision strategy;
- GLB export success;
- engine import success.

Vision-based comparison may suggest repairs, but it is not the final truth layer for geometric correctness.

---

## Change discipline

- Keep factories modular and readable.
- Avoid giant one-off scripts.
- Add a small example fixture and deterministic smoke test for every new factory family or contract feature.
- Prefer parameter patches over regenerating an entire asset during iterative visual repair.
- Add CI assertions that prove a new capability materially changes geometry or behavior when appropriate.
- Preserve regression targets for existing asset families.
- Keep environment staging, population metadata, and export geometry separable when they have different runtime responsibilities.
- Do not merge a visual improvement that breaks deterministic validation merely because the screenshot looks better.
- A Codex task is not complete because code was edited. It is complete only when the relevant tests and validation gates have been run and their result is reported accurately.

---

## Decision checklist for new work

Before implementing a requested visual change, ask:

1. Can an existing bounded parameter express it?
2. If not, is a reusable Semantic Macro the correct abstraction?
3. If not, does it require a new Room / Asset Factory?
4. Is it really a Style DNA concern shared by many assets?
5. Is it environment staging or population metadata rather than environment geometry?
6. Should this repeatable workflow become a Codex Skill?
7. If external execution is needed, should it be a typed/MCP tool rather than raw scripting?
8. How will CI prove the capability works?
9. How will the output remain game-ready and reproducible?

Only after those questions should free-form Blender scripting be considered as an engineering escape hatch.
