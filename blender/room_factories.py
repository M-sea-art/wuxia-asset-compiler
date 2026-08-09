"""Room-level factories for composable wuxia interiors.

These are intentionally coarse PoC modules. The compound factory decides layout;
each room factory owns only the objects inside its bay.
"""

from __future__ import annotations

from typing import Any, Callable

from primitives import add_box, add_cylinder


RoomFactory = Callable[[dict[str, Any], float, float, float, float, dict[str, Any]], None]


def _add_lanterns(
    prefix: str,
    center_x: float,
    width: float,
    depth: float,
    z0: float,
    wall_height: float,
    count: int,
    materials: dict[str, Any],
) -> None:
    if count <= 0:
        return
    spacing = width / (count + 1)
    for index in range(count):
        x = center_x - width / 2 + spacing * (index + 1)
        add_box(
            f"{prefix}_Lantern_{index:02d}",
            (x, -depth * 0.22, z0 + wall_height - 0.45),
            (0.24, 0.24, 0.36),
            materials["lantern"],
        )


def build_sect_gate_room(
    room: dict[str, Any],
    center_x: float,
    depth: float,
    z0: float,
    wall_height: float,
    materials: dict[str, Any],
) -> None:
    width = float(room["width"])
    opening = min(width * 0.58, 2.5)
    jamb = 0.22
    gate_height = min(wall_height * 0.78, 2.45)
    for sign in (-1, 1):
        add_box(
            "GateJamb",
            (center_x + sign * opening / 2, -depth / 2 + 0.22, z0 + gate_height / 2),
            (jamb, 0.28, gate_height),
            materials["wood"],
        )
    add_box(
        "GateLintel",
        (center_x, -depth / 2 + 0.22, z0 + gate_height),
        (opening + jamb * 2, 0.30, 0.22),
        materials["wood"],
    )
    add_box(
        "GateWeaponRack",
        (center_x - width * 0.31, -depth * 0.34, z0 + 0.72),
        (0.65, 0.28, 1.35),
        materials["wood"],
    )
    _add_lanterns(
        "Gate",
        center_x,
        width,
        depth,
        z0,
        wall_height,
        int(room.get("lantern_count", 2)),
        materials,
    )


def build_infirmary_rest_room(
    room: dict[str, Any],
    center_x: float,
    depth: float,
    z0: float,
    wall_height: float,
    materials: dict[str, Any],
) -> None:
    width = float(room["width"])
    add_box(
        "InfirmaryBed",
        (center_x - width * 0.15, -depth * 0.10, z0 + 0.38),
        (min(width * 0.62, 2.4), 1.25, 0.42),
        materials["wood"],
    )
    add_box(
        "InfirmaryMattress",
        (center_x - width * 0.15, -depth * 0.10, z0 + 0.62),
        (min(width * 0.58, 2.25), 1.12, 0.16),
        materials["cloth"],
    )
    add_box(
        "MedicineShelf",
        (center_x + width * 0.31, -depth / 2 + 0.40, z0 + 1.05),
        (0.72, 0.36, 1.75),
        materials["wood"],
    )
    add_box(
        "CareStool",
        (center_x + width * 0.14, depth * 0.08, z0 + 0.23),
        (0.48, 0.48, 0.46),
        materials["wood"],
    )
    _add_lanterns(
        "Infirmary",
        center_x,
        width,
        depth,
        z0,
        wall_height,
        int(room.get("lantern_count", 1)),
        materials,
    )


def build_kitchen_room(
    room: dict[str, Any],
    center_x: float,
    depth: float,
    z0: float,
    wall_height: float,
    materials: dict[str, Any],
) -> None:
    width = float(room["width"])
    add_box(
        "KitchenHearth",
        (center_x - width * 0.18, -depth * 0.18, z0 + 0.48),
        (1.25, 1.05, 0.96),
        materials["stone"],
    )
    add_cylinder(
        "KitchenPot",
        (center_x - width * 0.18, -depth * 0.18, z0 + 1.05),
        radius=0.48,
        depth=0.28,
        material=materials["metal"],
    )
    add_box(
        "KitchenPrepBench",
        (center_x + width * 0.20, -depth * 0.10, z0 + 0.78),
        (min(2.0, width * 0.44), 0.72, 0.12),
        materials["wood"],
    )
    add_box(
        "KitchenShelf",
        (center_x + width * 0.30, -depth / 2 + 0.38, z0 + 1.20),
        (min(1.5, width * 0.30), 0.34, 1.75),
        materials["wood"],
    )
    _add_lanterns(
        "Kitchen",
        center_x,
        width,
        depth,
        z0,
        wall_height,
        int(room.get("lantern_count", 1)),
        materials,
    )


def build_dining_room(
    room: dict[str, Any],
    center_x: float,
    depth: float,
    z0: float,
    wall_height: float,
    materials: dict[str, Any],
) -> None:
    width = float(room["width"])
    table_count = 2 if width >= 5.0 else 1
    for table_index in range(table_count):
        offset = (table_index - (table_count - 1) / 2) * min(2.5, width * 0.42)
        table_x = center_x + offset
        add_box(
            f"DiningTable_{table_index:02d}",
            (table_x, -depth * 0.02, z0 + 0.58),
            (1.75, 1.05, 0.12),
            materials["wood"],
        )
        for sx, sy in ((-0.68, -0.76), (0.68, -0.76), (-0.68, 0.76), (0.68, 0.76)):
            add_box(
                f"DiningStool_{table_index:02d}",
                (table_x + sx, -depth * 0.02 + sy, z0 + 0.22),
                (0.38, 0.38, 0.44),
                materials["wood"],
            )
    add_box(
        "DiningCupboard",
        (center_x + width * 0.34, -depth / 2 + 0.40, z0 + 1.02),
        (0.82, 0.36, 1.65),
        materials["wood"],
    )
    _add_lanterns(
        "Dining",
        center_x,
        width,
        depth,
        z0,
        wall_height,
        int(room.get("lantern_count", 2)),
        materials,
    )


ROOM_FACTORIES: dict[str, RoomFactory] = {
    "sect_gate_room": build_sect_gate_room,
    "infirmary_rest_room": build_infirmary_rest_room,
    "kitchen_room": build_kitchen_room,
    "dining_room": build_dining_room,
}
