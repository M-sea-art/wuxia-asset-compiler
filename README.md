# Wuxia Asset Compiler

Code-native, template-driven 3D asset compilation for stylized wuxia game worlds.

```text
reference image
    -> vision / scene spec
    -> style DNA + factory selection
    -> deterministic Blender generation
    -> multi-view preview + deterministic validation
    -> GLB
    -> game engine import
```

The project deliberately avoids making image-to-3D inference the default production path. A vision model should emit a compact, bounded `scene_spec.json`; deterministic Blender factories, Geometry Nodes, and reusable modules turn that specification into game-ready geometry.

The LLM should **not** generate hundreds of lines of ad-hoc `bpy` for every asset. Visual variety should come from factories, modules, seeds, bounded parameters, and a style-DNA layer.

## Current milestone

- One asset family: `cliff_kitchen`
- Versioned JSON Schema plus executable pure-Python contract
- Deterministic normalization of optional parameters
- Deterministic Blender Python factory
- Reusable materials and primitive modules
- One canonical preview or four fixed QA views
- Blender-side topology/transform/material/triangle validation report
- GLB export only after hard validation checks pass
- Zero-dependency scene-spec contract tests

## Repository layout

```text
compiler/
  spec.py
blender/
  build_asset.py
  factories.py
  validation.py
examples/
  cliff_kitchen.scene_spec.json
schema/
  scene_spec.schema.json
tests/
  test_scene_spec.py
```

## Compile an asset with Blender

From the repository root:

```powershell
blender --background --python blender/build_asset.py -- `
  --spec examples/cliff_kitchen.scene_spec.json `
  --out build/cliff_kitchen.glb `
  --preview build/cliff_kitchen.png `
  --preview-dir build/cliff_kitchen_views `
  --report build/cliff_kitchen.validation.json
```

`--preview-dir` renders fixed views at 45°, 135°, 225°, and 315°. These are intended to become the visual QA inputs for a reference-comparison agent.

The validation report currently records mesh/object counts, vertices, polygons, triangles, world bounds, non-manifold edges, zero-area faces, material-slot warnings, unapplied/negative scale, and triangle-budget warnings. Hard geometry failures stop GLB export.

On macOS/Linux, use `\` instead of PowerShell backticks for line continuation.

## Validate the scene-spec contract without Blender

```bash
python tests/test_scene_spec.py
```

The test verifies the example, normalization defaults, rejection of invalid/unknown parameters, and drift between the JSON Schema and executable runtime contract.

## Target architecture

```text
Reference Image
      |
      v
Reference Analyzer
      |
      v
Scene Spec / Asset DSL
      |
      +--> Style DNA
      |
      +--> Factory Resolver
               |
               v
        Blender execution layer
        (typed tools / Geometry Nodes / Python)
               |
               v
        Four-view preview capture
               |
               v
        Vision-assisted comparison
               |
               v
        Parameter patch
               |
               v
        Deterministic validation
               |
               v
              GLB
               |
               v
          Godot / other engines
```

## Near-term roadmap

1. Reference image -> `scene_spec.json` analyzer contract.
2. Parameter-only visual repair loop using the four fixed views.
3. GLB post-export validation and Godot import smoke test.
4. MCP macro tools such as `build_wuxia_asset`, `patch_asset_parameters`, and `validate_wuxia_asset`.
5. Factory families for roofs, timber halls, stone stairs, bridges, cliffs, vegetation, sect gates, and production buildings.
6. Style-DNA presets for coherent world-scale asset generation.
