"""Reusable deterministic prop macros for stylized wuxia interiors.

These are semantic building blocks above primitive geometry. Room factories should call
macros such as ``add_tall_storage`` and ``add_hearth_fire`` instead of duplicating raw
mesh operations. The macros remain deterministic and bounded by caller-provided values.
"""

from __future__ import annotations

import math
from typing import Any

from primitives import add_box, add_cone, add_cylinder, add_point_light


def add_tall_storage(
    prefix: str,
    *,
    center_x: float,
    y: float,
    z0: float,
    width: float,
    height: float,
    depth: float,
    rows: int,
    columns: int,
    stock_density: float,
    materials: dict[str, Any],
) -> None:
    """Build a tall shelf/cubby wall with deterministic visible stock."""
    rows = max(2, min(int(rows), 6))
    columns = max(1, min(int(columns), 5))
    stock_density = max(0.0, min(1.0, float(stock_density)))
    frame = 0.08
    shelf = 0.07

    add_box(
        f"{prefix}_Back",
        (center_x, y - depth * 0.42, z0 + height / 2),
        (width, frame, height),
        materials["wood"],
    )
    for sign in (-1, 1):
        add_box(
            f"{prefix}_Side",
            (center_x + sign * (width / 2 - frame / 2), y, z0 + height / 2),
            (frame, depth, height),
            materials["wood"],
        )

    row_h = height / rows
    for row in range(rows + 1):
        z = z0 + min(height, row * row_h)
        add_box(
            f"{prefix}_Shelf_{row:02d}",
            (center_x, y, z),
            (width, depth, shelf),
            materials["wood"],
        )

    col_w = width / columns
    for column in range(1, columns):
        x = center_x - width / 2 + column * col_w
        add_box(
            f"{prefix}_Divider_{column:02d}",
            (x, y, z0 + height / 2),
            (frame, depth * 0.88, height),
            materials["wood"],
        )

    total_cells = rows * columns
    for cell in range(total_cells):
        pseudo = ((cell * 37 + rows * 11 + columns * 17) % 100) / 100.0
        if pseudo >= stock_density:
            continue
        row = cell // columns
        column = cell % columns
        x = center_x - width / 2 + col_w * (column + 0.5)
        z = z0 + row_h * row + shelf * 0.8
        cell_span = col_w * 0.68
        variant = cell % 3
        if variant == 0:
            add_box(
                f"{prefix}_StockBox_{cell:02d}",
                (x, y + depth * 0.02, z + row_h * 0.20),
                (cell_span, depth * 0.52, max(0.12, row_h * 0.35)),
                materials["wood"],
            )
        else:
            radius = min(cell_span * 0.24, 0.13 + 0.015 * variant)
            add_cylinder(
                f"{prefix}_StockJar_{cell:02d}",
                (x, y + depth * 0.04, z + radius),
                radius=radius,
                depth=radius * (1.8 + 0.2 * variant),
                material=materials["ceramic"],
            )


def add_drawer_cabinet(
    prefix: str,
    *,
    center_x: float,
    y: float,
    z0: float,
    width: float,
    height: float,
    depth: float,
    rows: int,
    columns: int,
    materials: dict[str, Any],
) -> None:
    """Build a shallow apothecary-style drawer cabinet."""
    rows = max(2, min(int(rows), 6))
    columns = max(2, min(int(columns), 6))
    add_box(
        f"{prefix}_CabinetBody",
        (center_x, y, z0 + height / 2),
        (width, depth, height),
        materials["wood"],
    )
    cell_w = width / columns
    cell_h = height / rows
    front_y = y + depth / 2 + 0.012
    for row in range(rows):
        for column in range(columns):
            x = center_x - width / 2 + cell_w * (column + 0.5)
            z = z0 + cell_h * (row + 0.5)
            add_box(
                f"{prefix}_Drawer_{row:02d}_{column:02d}",
                (x, front_y, z),
                (cell_w * 0.82, 0.035, cell_h * 0.74),
                materials["wood_detail"],
            )
            add_cylinder(
                f"{prefix}_Pull_{row:02d}_{column:02d}",
                (x, front_y + 0.035, z),
                radius=0.022,
                depth=0.05,
                material=materials["metal"],
                rotation=(math.radians(90), 0.0, 0.0),
                vertices=8,
            )


def add_hanging_cookware_rack(
    prefix: str,
    *,
    center_x: float,
    y: float,
    z_top: float,
    span: float,
    count: int,
    materials: dict[str, Any],
) -> None:
    """Build a suspended timber rail with hanging pans/pots."""
    count = max(1, min(int(count), 8))
    add_box(
        f"{prefix}_Rail",
        (center_x, y, z_top),
        (span, 0.10, 0.12),
        materials["wood"],
    )
    spacing = span / (count + 1)
    for index in range(count):
        x = center_x - span / 2 + spacing * (index + 1)
        drop = 0.36 + 0.10 * (index % 3)
        add_box(
            f"{prefix}_Cord_{index:02d}",
            (x, y, z_top - drop / 2),
            (0.025, 0.025, drop),
            materials["rope"],
        )
        radius = 0.13 + 0.025 * (index % 2)
        add_cylinder(
            f"{prefix}_Cookware_{index:02d}",
            (x, y, z_top - drop - 0.03),
            radius=radius,
            depth=0.075,
            material=materials["metal"],
            rotation=(math.radians(90), 0.0, 0.0),
        )
        if index % 2 == 0:
            add_box(
                f"{prefix}_Handle_{index:02d}",
                (x + radius * 0.95, y, z_top - drop - 0.03),
                (radius * 1.35, 0.045, 0.045),
                materials["metal"],
                rotation=(0.0, 0.0, math.radians(18 * ((index % 3) - 1))),
            )


def add_hearth_fire(
    prefix: str,
    *,
    center_x: float,
    y: float,
    z0: float,
    intensity: float,
    materials: dict[str, Any],
) -> None:
    """Add stylized emissive flame geometry and a local warm light."""
    intensity = max(0.0, min(1.0, float(intensity)))
    flame_count = 3 + int(round(intensity * 3))
    for index in range(flame_count):
        angle = (index / max(flame_count, 1)) * math.tau
        radius = 0.10 + 0.025 * (index % 2)
        height = 0.32 + 0.13 * ((index * 2) % 3) + 0.18 * intensity
        x = center_x + math.cos(angle) * 0.15
        yy = y + math.sin(angle) * 0.10
        add_cone(
            f"{prefix}_Flame_{index:02d}",
            (x, yy, z0 + height / 2),
            radius1=radius,
            radius2=0.015,
            depth=height,
            material=materials["fire"],
        )
    add_point_light(
        f"{prefix}_FireLight",
        (center_x, y + 0.06, z0 + 0.28),
        energy=160.0 + intensity * 230.0,
        color=(1.0, 0.24, 0.04),
        radius=0.45,
    )


def add_basket_cluster(
    prefix: str,
    *,
    center_x: float,
    y: float,
    z0: float,
    count: int,
    span: float,
    materials: dict[str, Any],
) -> None:
    count = max(1, min(int(count), 8))
    spacing = span / max(count, 1)
    start = center_x - span / 2 + spacing / 2
    for index in range(count):
        radius = 0.16 + 0.02 * (index % 3)
        add_cylinder(
            f"{prefix}_Basket_{index:02d}",
            (start + spacing * index, y, z0 + 0.11),
            radius=radius,
            depth=0.22,
            material=materials["basket"],
            vertices=10,
        )
        for item in range(2 + index % 3):
            add_box(
                f"{prefix}_Produce_{index:02d}_{item:02d}",
                (
                    start + spacing * index + (item - 1) * 0.055,
                    y,
                    z0 + 0.24 + 0.035 * (item % 2),
                ),
                (0.08, 0.08, 0.10),
                materials["produce"],
            )
