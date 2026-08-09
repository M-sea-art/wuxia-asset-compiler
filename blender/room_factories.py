"""Room-level factories for composable wuxia interiors.

The compound factory decides layout; each room factory owns the objects inside its bay.
Room-level parameters must materially change deterministic geometry so a vision repair
loop can improve semantic density without asking an LLM to rewrite Blender code.
"""

from __future__ import annotations

from typing import Any, Callable

from primitives import add_box, add_cylinder


RoomFactory = Callable[[dict[str, Any], float, float, float, float, dict[str, Any]], None]


def _clutter_count(room: dict[str, Any], minimum: int, maximum: int) -> int:
    clutter = max(0.0, min(1.0, float(room.get("clutter", 0.5))))
    return int(round(minimum + (maximum - minimum) * clutter))


def _occupancy(room: dict[str, Any]) -> int:
    return max(0, int(room.get("occupancy", 0)))


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


def _add_backwall_boxes(
    prefix: str,
    center_x: float,
    width: float,
    depth: float,
    z0: float,
    count: int,
    materials: dict[str, Any],
) -> None:
    if count <= 0:
        return
    usable = max(0.6, width * 0.68)
    spacing = usable / max(count, 1)
    start = center_x - usable / 2 + spacing / 2
    for index in range(count):
        x = start + spacing * index
        scale = 0.28 + 0.05 * (index % 3)
        add_box(
            f"{prefix}_Storage_{index:02d}",
            (x, -depth / 2 + 0.52, z0 + scale / 2),
            (scale * 1.25, 0.34, scale),
            materials["wood"],
        )


def _add_container_row(
    prefix: str,
    center_x: float,
    span: float,
    y: float,
    z: float,
    count: int,
    materials: dict[str, Any],
    material_key: str = "stone",
) -> None:
    if count <= 0:
        return
    spacing = span / max(count, 1)
    start = center_x - span / 2 + spacing / 2
    for index in range(count):
        radius = 0.10 + 0.02 * (index % 3)
        add_cylinder(
            f"{prefix}_Container_{index:02d}",
            (start + spacing * index, y, z + radius),
            radius=radius,
            depth=radius * 1.8,
            material=materials[material_key],
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

    _add_backwall_boxes(
        "Gate",
        center_x + width * 0.08,
        width * 0.70,
        depth,
        z0,
        _clutter_count(room, 1, 5),
        materials,
    )
    for index in range(min(_occupancy(room), 3)):
        add_box(
            f"GateWaitingStool_{index:02d}",
            (center_x - width * 0.18 + index * 0.52, depth * 0.12, z0 + 0.21),
            (0.38, 0.38, 0.42),
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
    bed_x = center_x - width * 0.15
    add_box(
        "InfirmaryBed",
        (bed_x, -depth * 0.10, z0 + 0.38),
        (min(width * 0.62, 2.4), 1.25, 0.42),
        materials["wood"],
    )
    add_box(
        "InfirmaryMattress",
        (bed_x, -depth * 0.10, z0 + 0.62),
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

    jar_count = _clutter_count(room, 2, 9)
    _add_container_row(
        "InfirmaryMedicine",
        center_x + width * 0.22,
        min(width * 0.38, 1.45),
        -depth / 2 + 0.18,
        z0 + 1.18,
        jar_count,
        materials,
    )
    bundle_count = max(1, min(_occupancy(room), 4))
    for index in range(bundle_count):
        add_box(
            f"InfirmaryBedding_{index:02d}",
            (bed_x - 0.45 + index * 0.30, -depth * 0.10, z0 + 0.76 + 0.04 * index),
            (0.34, 0.42, 0.12),
            materials["cloth"],
        )
    _add_backwall_boxes(
        "Infirmary",
        center_x - width * 0.20,
        width * 0.35,
        depth,
        z0,
        _clutter_count(room, 1, 4),
        materials,
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
    hearth_x = center_x - width * 0.18
    prep_x = center_x + width * 0.20
    add_box(
        "KitchenHearth",
        (hearth_x, -depth * 0.18, z0 + 0.48),
        (1.25, 1.05, 0.96),
        materials["stone"],
    )
    add_cylinder(
        "KitchenPot",
        (hearth_x, -depth * 0.18, z0 + 1.05),
        radius=0.48,
        depth=0.28,
        material=materials["metal"],
    )
    add_box(
        "KitchenPrepBench",
        (prep_x, -depth * 0.10, z0 + 0.78),
        (min(2.0, width * 0.44), 0.72, 0.12),
        materials["wood"],
    )
    add_box(
        "KitchenShelf",
        (center_x + width * 0.30, -depth / 2 + 0.38, z0 + 1.20),
        (min(1.5, width * 0.30), 0.34, 1.75),
        materials["wood"],
    )

    jar_count = _clutter_count(room, 4, 14)
    _add_container_row(
        "KitchenJar",
        center_x + width * 0.22,
        min(width * 0.42, 2.0),
        -depth / 2 + 0.18,
        z0 + 0.82,
        jar_count,
        materials,
    )
    prep_count = min(max(_occupancy(room), 1), 6)
    _add_container_row(
        "KitchenPrepBowl",
        prep_x,
        min(width * 0.34, 1.65),
        -depth * 0.10,
        z0 + 0.84,
        prep_count,
        materials,
    )
    _add_backwall_boxes(
        "Kitchen",
        center_x - width * 0.03,
        width * 0.82,
        depth,
        z0,
        _clutter_count(room, 2, 7),
        materials,
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
    table_positions: list[float] = []
    for table_index in range(table_count):
        offset = (table_index - (table_count - 1) / 2) * min(2.5, width * 0.42)
        table_x = center_x + offset
        table_positions.append(table_x)
        add_box(
            f"DiningTable_{table_index:02d}",
            (table_x, -depth * 0.02, z0 + 0.58),
            (1.75, 1.05, 0.12),
            materials["wood"],
        )

    seat_slots = []
    for table_x in table_positions:
        seat_slots.extend(
            [
                (table_x - 0.68, -depth * 0.02 - 0.76),
                (table_x + 0.68, -depth * 0.02 - 0.76),
                (table_x - 0.68, -depth * 0.02 + 0.76),
                (table_x + 0.68, -depth * 0.02 + 0.76),
            ]
        )
    stool_count = min(max(_occupancy(room), 4), len(seat_slots))
    for index, (x, y) in enumerate(seat_slots[:stool_count]):
        add_box(
            f"DiningStool_{index:02d}",
            (x, y, z0 + 0.22),
            (0.38, 0.38, 0.44),
            materials["wood"],
        )

    place_count = min(max(_occupancy(room), 2), table_count * 6)
    for index in range(place_count):
        table_x = table_positions[index % table_count]
        local_index = index // table_count
        local_x = (-0.48, 0.0, 0.48)[local_index % 3]
        local_y = -0.18 if (local_index // 3) % 2 == 0 else 0.18
        add_cylinder(
            f"DiningBowl_{index:02d}",
            (table_x + local_x, -depth * 0.02 + local_y, z0 + 0.68),
            radius=0.12,
            depth=0.08,
            material=materials["stone"],
        )

    add_box(
        "DiningCupboard",
        (center_x + width * 0.34, -depth / 2 + 0.40, z0 + 1.02),
        (0.82, 0.36, 1.65),
        materials["wood"],
    )
    _add_container_row(
        "DiningCrockery",
        center_x + width * 0.16,
        min(width * 0.55, 2.8),
        -depth / 2 + 0.18,
        z0 + 0.92,
        _clutter_count(room, 3, 12),
        materials,
    )
    _add_backwall_boxes(
        "Dining",
        center_x - width * 0.16,
        width * 0.52,
        depth,
        z0,
        _clutter_count(room, 1, 5),
        materials,
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
