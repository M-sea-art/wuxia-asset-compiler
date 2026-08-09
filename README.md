# Wuxia Asset Compiler

**Code-native, template-driven 3D asset compilation for stylized wuxia and eastern-fantasy game worlds.**

> The goal is not to ask an AI to reinvent a Blender scene from scratch every time.  
> The goal is to turn visual intent into a bounded specification, compile it through reusable world rules, validate the result, and keep every improvement as a reusable capability.

📖 **中文项目宗旨与理念：[`docs/PROJECT_PHILOSOPHY.zh-CN.md`](docs/PROJECT_PHILOSOPHY.zh-CN.md)**

---

## What this project is trying to build

Wuxia Asset Compiler treats 3D asset production as a **compiler problem**:

```text
Reference image / art direction
        ↓
Vision interpretation
        ↓
reference_analysis.json
        ↓
Deterministic resolver
        ↓
scene_spec.json / Asset DSL
        ↓
Factory selection + Style DNA
        ↓
Semantic Macros + Blender execution
        ↓
Render / multi-view QA
        ↓
Bounded parameter repair OR template_gap
        ↓
Deterministic geometry validation
        ↓
GLB
        ↓
Godot / other game engines
```

The project deliberately avoids making expensive image-to-3D inference the permanent default production path. Image-to-3D systems can still be useful as **teachers, bootstrap tools, or reference generators**, but repeated production should increasingly come from reusable factories, modules, parameters, seeds, and style rules.

---

## Core philosophy

### The model interprets; deterministic code owns geometry truth

LLM/VLM responsibilities:

- understand references and intent;
- classify scene / room semantics;
- estimate bounded parameters with confidence and evidence;
- compare renders to references;
- propose repairs;
- identify missing compiler capabilities.

Deterministic code responsibilities:

- schema and parameter ownership;
- accepting or rejecting model proposals;
- geometry construction;
- measurements and topology checks;
- export readiness;
- reproducibility.

A model may say that two beams *look* connected. If deterministic measurement says there is a gap, the measurement wins.

### The reusable capability is more valuable than the one-off mesh

The project scales through this ladder:

```text
Primitive
  ↓
Semantic Macro
  ↓
Room / Asset Factory
  ↓
Compound Factory
  ↓
Style DNA
  ↓
World-scale assembly
```

A visual failure should ideally leave the compiler stronger. If the reference contains something the current DSL cannot express, Visual QA emits a **`template_gap`** instead of forcing unrelated parameters to extreme values.

### Style is a system, not a prompt suffix

World coherence should eventually live in Style DNA: proportions, structural rhythm, roof language, material families, aging ranges, prop density, lighting contrast, ornament, environment staging, and population behavior slots.

---

## What is already implemented

The repository currently proves an end-to-end bounded pipeline rather than only a hand-written Blender demo:

- versioned pure-Python Scene Spec contract;
- reference-analysis contract with confidence + evidence;
- deterministic reference resolver;
- global and room-level bounded parameter patches;
- reusable room factories;
- reusable semantic prop macros;
- front cutaway preview plus four fixed QA views;
- visual-review contract;
- bounded visual-repair pass;
- explicit `template_gap` reporting;
- deterministic Blender geometry validation;
- GLB export only after hard validation passes;
- GitHub Actions smoke tests that run Blender headlessly;
- regression coverage for the original `cliff_kitchen` asset family.

The current mother-reference experiment includes a composable cliff ground floor with gate, infirmary, kitchen, and dining-room semantics. Recent semantic macros add tall stocked shelving, apothecary drawers, hanging cookware, ingredient baskets, and a controlled hearth-fire module.

This is still a **prototype compiler**, not a claim of photoreal one-click reconstruction.

---

## What this project is not

Wuxia Asset Compiler is **not** intended to be:

- a universal “any image → perfect 3D” system;
- a photogrammetry / NeRF / Gaussian-splat replacement;
- an unrestricted autonomous `bpy` execution environment;
- a collection of prompts that regenerates every asset from zero;
- a tool for copying protected characters, faction marks, locations, or distinctive art from existing martial-arts IP;
- a promise that art direction and engineering judgment can be removed from production.

It is optimized for **fixed visual languages, modular worlds, repeatable game assets, and families of related variations**.

---

## Repository layout

```text
analyzer/
  reference.py            # bounded vision-analysis contract and resolver

compiler/
  spec.py                 # executable Scene Spec contract
  templates.py            # deterministic base templates

qa/
  visual_review.py        # bounded visual QA / repair contract

blender/
  build_asset.py          # Blender CLI entry point
  primitives.py           # low-level deterministic geometry helpers
  prop_macros.py          # reusable semantic modeling macros
  room_factories.py       # room-level composition
  ground_floor_factory.py # multi-room compound slice
  factories.py            # shared asset factory helpers
  validation.py           # topology / transform / budget validation

tools/
  resolve_reference.py    # reference analysis → Scene Spec
  apply_visual_review.py  # QA review → repaired Scene Spec

examples/                 # specs, analyses, and captured QA fixtures
schema/                   # JSON Schemas
tests/                    # zero-dependency compiler contract tests
.github/workflows/        # pure-Python + headless Blender smoke CI
```

---

## Example workflow

### 1. Resolve a captured reference analysis

```bash
python tools/resolve_reference.py \
  --analysis examples/cliff_ground_floor.reference_analysis.json \
  --out build/reference/cliff_ground_floor.scene_spec.json \
  --report build/reference/cliff_ground_floor.resolution.json \
  --seed 23 \
  --minimum-confidence 0.35
```

### 2. Compile the resolved Scene Spec in Blender

```bash
blender --background --python blender/build_asset.py -- \
  --spec build/reference/cliff_ground_floor.scene_spec.json \
  --out build/cliff_ground_floor.glb \
  --preview build/cliff_ground_floor.png \
  --preview-dir build/cliff_ground_floor_views \
  --report build/cliff_ground_floor.validation.json
```

### 3. Apply a bounded visual-review patch

```bash
python tools/apply_visual_review.py \
  --spec build/reference/cliff_ground_floor.scene_spec.json \
  --review examples/cliff_ground_floor.visual_review.json \
  --out build/repair/cliff_ground_floor.scene_spec.json \
  --report build/repair/cliff_ground_floor.repair.json \
  --minimum-confidence 0.40
```

Then compile the repaired spec with the same Blender command.

---

## Validation philosophy

Visual similarity is useful, but it is **not the final truth layer** for game assets.

Before an asset is considered production-ready, the pipeline should eventually verify at least:

- dimensions and world scale;
- transforms and pivot/origin;
- mesh / triangle budgets;
- degenerate and non-manifold geometry;
- normals;
- UV requirements;
- material slots and texture references;
- collision strategy;
- GLB validity;
- game-engine import success.

The compiler should prefer a slightly less visually similar but clean, editable, reproducible, engine-ready asset over an opaque one-off mesh that cannot survive production.

---

## Development decision rule

When a reference does not match the render, ask in this order:

1. **Is the existing parameter wrong?** → bounded patch.
2. **Is a reusable semantic Macro missing?** → add one.
3. **Is a Room / Asset Factory missing?** → add one.
4. **Is the Style DNA incomplete?** → extend the style system.
5. Only use free-form Blender scripting as a narrow engineering escape hatch, not the normal agent interface.

This rule is intended to make every iteration accumulate reusable capability instead of accumulating prompt debt.

---

## Near-term roadmap

- character-slot population pass with Blender QA proxies and engine spawn metadata;
- infirmary cloth / bedding / care-prop macros;
- wuxia structural ornament and railing / bracket language;
- atmospheric staging with mist, bamboo, moon fill, and distant mountain layers;
- richer Style DNA contracts;
- GLB post-export validation and Godot import smoke tests;
- higher-level MCP / agent workflows around stable compiler operations;
- additional factory families for roofs, halls, gates, bridges, cliffs, vegetation, roads, and full sect compounds.

---

## Long-term vision

The long-term target is not “generate one building.”

It is a reusable **eastern-fantasy world asset compiler** capable of turning art direction into coherent families of sect gates, cliff dwellings, kitchens, apothecaries, bridges, bamboo groves, mountain paths, villages, and eventually full compounds and settlements.

**Let AI understand the world. Let templates preserve its rules. Let Blender compile those rules into spaces a game can actually use.**
