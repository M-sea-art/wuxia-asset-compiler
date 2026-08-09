"""Zero-dependency contract smoke test for the example Wuxia scene spec."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "examples" / "cliff_kitchen.scene_spec.json"


def main() -> None:
    data = json.loads(SPEC.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["factory"] == "cliff_kitchen"
    assert isinstance(data["seed"], int) and data["seed"] >= 0

    parameters = data["parameters"]
    required = {
        "width",
        "depth",
        "wall_height",
        "roof_pitch_deg",
        "eave_overhang",
        "platform_height",
        "cliff_embed",
        "stone_step_count",
    }
    missing = required - parameters.keys()
    assert not missing, f"missing parameters: {sorted(missing)}"
    assert 3.0 <= parameters["width"] <= 20.0
    assert 2.5 <= parameters["depth"] <= 14.0
    assert 15.0 <= parameters["roof_pitch_deg"] <= 55.0
    assert 0.0 <= parameters["cliff_embed"] <= 1.0
    assert 3 <= parameters["stone_step_count"] <= 30

    style = data["style"]
    assert style["palette"] == "paper_ink_old_wood"
    print("scene_spec smoke test: PASS")


if __name__ == "__main__":
    main()
