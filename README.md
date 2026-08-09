# Wuxia Asset Compiler

Code-native, template-driven 3D asset compilation for stylized wuxia game worlds.

```text
reference image
    -> vision / scene spec
    -> style DNA + factory selection
    -> deterministic Blender generation
    -> preview + validation
    -> GLB
    -> game engine import
```

The project deliberately avoids making image-to-3D inference the default production path. A vision model should emit a compact, bounded `scene_spec.json`; deterministic Blender factories, Geometry Nodes, and reusable modules turn that specification into game-ready geometry.

## Current milestone: PoC-0

- One asset family: `cliff_kitchen`
- Versioned scene-spec contract
- Deterministic Blender Python factory
- Reusable materials and primitive modules
- Fixed isometric preview camera and lighting
- GLB export entry point
- Zero-dependency scene-spec smoke test

The LLM should **not** generate hundreds of lines of ad-hoc `bpy` for every asset. Visual variety should come from factories, modules, seeds, bounded parameters, and later a style-DNA layer.

## Repository layout

```text
blender/
  build_asset.py
  factories.py
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
  --preview build/cliff_kitchen.png
```

On macOS/Linux, use `\` instead of PowerShell backticks for line continuation.

## Validate the example spec without Blender

```bash
python tests/test_scene_spec.py
```

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
        Multi-view preview capture
               |
               v
        Vision-assisted comparison
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
2. Four fixed preview views and parameter-only visual repair loop.
3. Deterministic geometry, topology, transform, material, and GLB validation.
4. Godot import smoke test.
5. MCP macro tools such as `build_wuxia_asset`, `patch_asset_parameters`, and `validate_wuxia_asset`.
6. Factory families for roofs, timber halls, stone stairs, bridges, cliffs, vegetation, sect gates, and production buildings.
7. Style-DNA presets for coherent world-scale asset generation.
