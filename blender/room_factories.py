"""Room-level factories for composable wuxia interiors.

The compound factory decides layout; each room factory owns the objects inside its bay.
Room-level parameters materially change deterministic geometry, while reusable semantic
prop macros supply vertical storage, cabinets, hearth fire, hanging cookware and baskets.
"""

from __future__ import annotations

from typing import Any, Callable

from primitives import add_box, add_cylinder
from prop_macros import (
    add_basket_cluster,
    add_drawer_cabinet,
    add_hanging_cookware_rack,
    add_hearth_fire,
    add_tall_storage,
)


RoomFactory = Callable[[dict[str, Any], float, float, float, float, dict[str, Any]], None]


def _clutter(room: dict[str, Any]) -> float:
    return max(0.0, min(1.0, float(room.get("clutter", 0.5))))


def _clutter_count(room: dict[str, Any], minimum: int, maximum: int) -> int:
    return int(round(minimum + (maximum - minimum) * _clutter(room)))


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
    material_key: str = "ceramic",
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

    add_tall_storage(
        "GateTallStorage",
        center_x=center_x + width * 0.31,
        y=-depth / 2 + 0.42,
        z0=z0 + 0.04,
        width=min(1.05, width * 0.26),
        height=min(1.95, wall_height * 0.72),
        depth=0.38,
        rows=4,
        columns=2,
        stock_density=_clutter(room) * 0.72,
        materials=materials,
    )
    _add_backwall_boxes(
        "Gate",
        center_x + width * 0.02,
        width * 0.48,
        depth,
        z0,
        _clutter_count(room, 1, 4),
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
    bed_x = center_x - width * 0.17
    add_box(
        "InfirmaryBed",
        (bed_x, -depth * 0.08, z0 + 0.38),
        (min(width * 0.58, 2.35), 1.25, 0.42),
        materials["wood"],
    )
    add_box(
        "InfirmaryMattress",
        (bed_x, -depth * 0.08, z0 + 0.62),
        (min(width * 0.55, 2.20), 1.12, 0.16),
        materials["cloth"],
    )
    add_box(
        "CareStool",
        (center_x + width * 0.06, depth * 0.12, z0 + 0.23),
        (0.48, 0.48, 0.46),
        materials["wood"],
    )

    add_drawer_cabinet(
        "InfirmaryDrawerCabinet",
        center_x=center_x + width * 0.31,
        y=-depth / 2 + 0.38,
        z0=z0 + 0.05,
        width=min(1.10, width * 0.28),
        height=1.42,
        depth=0.36,
        rows=4,
        columns=3,
        materials=materials,
    )
    add_tall_storage(
        "InfirmaryTallShelf",
        center_x=center_x + width * 0.13,
        y=-depth / 2 + 0.43,
        z0=z0 + 0.05,
        width=min(0.92, width * 0.22),
        height=min(2.10, wall_height * 0.76),
        depth=0.36,
        rows=5,
        columns=2,
        stock_density=_clutter(room),
        materials=materials,
    )

    jar_count = _clutter_count(room, 3, 10)
    _add_container_row(
        "InfirmaryMedicine",
        center_x + width * 0.20,
        min(width * 0.34, 1.25),
        -depth / 2 + 0.18,
        z0 + 1.52,
        jar_count,
        materials,
    )
    bundle_count = max(1, min(_occupancy(room) + 1, 5))
    for index in range(bundle_count):
        add_box(
            f"InfirmaryBedding_{index:02d}",
            (bed_x - 0.46 + index * 0.26, -depth * 0.08, z0 + 0.76 + 0.04 * index),
            (0.34, 0.42, 0.12),
            materials["cloth"],
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
    clutter = _clutter(room)
    hearth_x = center_x - width * 0.16
    prep_x = center_x + width * 0.19

    add_box(
        "KitchenHearth",
        (hearth_x, -depth * 0.16, z0 + 0.48),
        (1.32, 1.08, 0.96),
        materials["stone"],
    )
    add_cylinder(
        "KitchenPot",
        (hearth_x, -depth * 0.16, z0 + 1.05),
        radius=0.49,
        depth=0.28,
        material=materials["metal"],
    )
    add_hearth_fire(
        "KitchenHearth",
        center_x=hearth_x,
        y=-depth * 0.16 + 0.40,
        z0=z0 + 0.48,
        intensity=0.62 + clutter * 0.36,
        materials=materials,
    )

    add_box(
        "KitchenPrepBench",
        (prep_x, -depth * 0.02, z0 + 0.78),
        (min(2.15, width * 0.42), 0.76, 0.12),
        materials["wood"],
    )
    add_tall_storage(
        "KitchenTallShelf",
        center_x=center_x + width * 0.31,
        y=-depth / 2 + 0.44,
        z0=z0 + 0.04,
        width=min(1.45, width * 0.28),
        height=min(2.28, wall_height * 0.80),
        depth=0.42,
        rows=5,
        columns=3,
        stock_density=clutter,
        materials=materials,
    )
    add_tall_storage(
        "KitchenPotShelf",
        center_x=center_x - width * 0.34,
        y=-depth / 2 + 0.44,
        z0=z0 + 0.04,
        width=min(1.05, width * 0.20),
        height=min(1.92, wall_height * 0.68),
        depth=0.40,
        rows=4,
        columns=2,
        stock_density=0.55 + clutter * 0.40,
        materials=materials,
    )
    add_hanging_cookware_rack(
        "KitchenHangingRack",
        center_x=center_x - width * 0.03,
        y=-depth * 0.26,
        z_top=z0 + wall_height * 0.76,
        span=min(width * 0.48, 2.55),
        count=_clutter_count(room, 3, 7),
        materials=materials,
    )

    jar_count = _clutter_count(room, 5, 15)
    _add_container_row(
        "KitchenJar",
        center_x + width * 0.12,
        min(width * 0.34, 1.75),
        -depth / 2 + 0.18,
        z0 + 0.70,
        jar_count,
        materials,
    )
    prep_count = min(max(_occupancy(room) + 1, 2), 7)
    _add_container_row(
        "KitchenPrepBowl",
        prep_x,
        min(width * 0.34, 1.70),
        -depth * 0.02,
        z0 + 0.84,
        prep_count,
        materials,
    )
    add_basket_cluster(
        "KitchenIngredients",
        center_x=center_x + width * 0.02,
        y=depth * 0.22,
        z0=z0 + 0.05,
        count=_clutter_count(room, 2, 6),
        span=min(width * 0.44, 2.2),
        materials=materials,
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
    clutter = _clutter(room)
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
            material=materials["ceramic"],
        )

    add_drawer_cabinet(
        "DiningDrawerCabinet",
        center_x=center_x + width * 0.34,
        y=-depth / 2 + 0.39,
        z0=z0 + 0.04,
        width=min(1.20, width * 0.22),
        height=1.45,
        depth=0.36,
        rows=3,
        columns=3,
        materials=materials,
    )
    add_tall_storage(
        "DiningTallShelf",
        center_x=center_x - width * 0.31,
        y=-depth / 2 + 0.44,
        z0=z0 + 0.04,
        width=min(1.55, width * 0.26),
        height=min(2.22, wall_height * 0.78),
        depth=0.42,
        rows=5,
        columns=3,
        stock_density=clutter,
        materials=materials,
    )
    _add_container_row(
        "DiningCrockery",
        center_x + width * 0.10,
        min(width * 0.42, 2.30),
        -depth / 2 + 0.18,
        z0 + 0.92,
        _clutter_count(room, 4, 13),
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
