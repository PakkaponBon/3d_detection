#!/usr/bin/env python3

from pathlib import Path
import math

OUT = Path.home() / "amr_ws/src/my_first_bot/worlds/fuel_warehouse.world"


def pose_from_local(base_x, base_y, yaw, lx, ly):
    wx = base_x + lx * math.cos(yaw) - ly * math.sin(yaw)
    wy = base_y + lx * math.sin(yaw) + ly * math.cos(yaw)
    return wx, wy


def simple_box_model(name, x, y, z, sx, sy, sz, color="0.7 0.45 0.18 1"):
    return f"""
    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} {z} 0 0 0</pose>
      <link name="link">
        <visual name="visual">
          <geometry>
            <box><size>{sx} {sy} {sz}</size></box>
          </geometry>
          <material>
            <ambient>{color}</ambient>
            <diffuse>{color}</diffuse>
          </material>
        </visual>
        <collision name="collision">
          <geometry>
            <box><size>{sx} {sy} {sz}</size></box>
          </geometry>
        </collision>
      </link>
    </model>
"""


def marker_box(name, x, y, z, sx, sy, sz, color="0 1 0 0.4"):
    return f"""
    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} {z} 0 0 0</pose>
      <link name="link">
        <visual name="visual">
          <geometry>
            <box><size>{sx} {sy} {sz}</size></box>
          </geometry>
          <material>
            <ambient>{color}</ambient>
            <diffuse>{color}</diffuse>
          </material>
        </visual>
      </link>
    </model>
"""


def rack_model(name, x, y, yaw=0.0, length=4.8, depth=0.7):
    yellow = "0.95 0.85 0.15 1"
    black = "0.07 0.07 0.07 1"
    blue = "0.25 0.35 0.8 1"

    parts = [f"""
    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} 0 0 0 {yaw}</pose>
"""]

    # shelf decks
    for level, z in enumerate([0.55, 1.25, 1.95]):
        parts.append(f"""
      <link name="deck_{level}">
        <pose>0 0 {z} 0 0 0</pose>
        <visual name="visual">
          <geometry>
            <box><size>{length} {depth} 0.08</size></box>
          </geometry>
          <material>
            <ambient>{yellow}</ambient>
            <diffuse>{yellow}</diffuse>
          </material>
        </visual>
        <collision name="collision">
          <geometry>
            <box><size>{length} {depth} 0.08</size></box>
          </geometry>
        </collision>
      </link>
""")

    # side frames / legs
    leg_xs = [-length/2, -length/6, length/6, length/2]
    for i, lx in enumerate(leg_xs):
        for side, ly in enumerate([-depth/2 + 0.04, depth/2 - 0.04]):
            parts.append(f"""
      <link name="leg_{i}_{side}">
        <pose>{lx} {ly} 1.0 0 0 0</pose>
        <visual name="visual">
          <geometry>
            <box><size>0.08 0.08 2.0</size></box>
          </geometry>
          <material>
            <ambient>{black}</ambient>
            <diffuse>{black}</diffuse>
          </material>
        </visual>
        <collision name="collision">
          <geometry>
            <box><size>0.08 0.08 2.0</size></box>
          </geometry>
        </collision>
      </link>
""")

    # top frame beam
    parts.append(f"""
      <link name="top_beam">
        <pose>0 0 2.25 0 0 0</pose>
        <visual name="visual">
          <geometry>
            <box><size>{length} 0.06 0.06</size></box>
          </geometry>
          <material>
            <ambient>{blue}</ambient>
            <diffuse>{blue}</diffuse>
          </material>
        </visual>
      </link>
""")

    parts.append("    </model>\n")
    return "".join(parts)


def boxes_on_rack(prefix, rack_x, rack_y, rack_yaw, rack_length=4.8):
    result = ""
    idx = 0

    local_xs = [-1.8, -1.2, -0.6, 0.0, 0.6, 1.2, 1.8]
    levels = [0.68, 1.38, 2.08]

    for z in levels:
        for lx in local_xs:
            for ly in [-0.12, 0.12]:
                wx, wy = pose_from_local(rack_x, rack_y, rack_yaw, lx, ly)
                sx = 0.38
                sy = 0.28
                sz = 0.22
                result += simple_box_model(
                    f"{prefix}_box_{idx}",
                    wx, wy, z,
                    sx, sy, sz,
                    color="0.73 0.58 0.34 1"
                )
                idx += 1
    return result


def low_center_rack(name, x, y, yaw=0.0, length=1.5, depth=0.55, height=0.45):
    yellow = "0.95 0.85 0.15 1"
    black = "0.08 0.08 0.08 1"

    return f"""
    <model name="{name}">
      <static>true</static>
      <pose>{x} {y} 0 0 0 {yaw}</pose>
      <link name="link">
        <visual name="top">
          <pose>0 0 {height} 0 0 0</pose>
          <geometry>
            <box><size>{length} {depth} 0.06</size></box>
          </geometry>
          <material>
            <ambient>{yellow}</ambient>
            <diffuse>{yellow}</diffuse>
          </material>
        </visual>

        <visual name="leg1">
          <pose>{-length/2 + 0.05} 0 {height/2} 0 0 0</pose>
          <geometry>
            <box><size>0.06 0.06 {height}</size></box>
          </geometry>
          <material>
            <ambient>{black}</ambient>
            <diffuse>{black}</diffuse>
          </material>
        </visual>

        <visual name="leg2">
          <pose>{length/2 - 0.05} 0 {height/2} 0 0 0</pose>
          <geometry>
            <box><size>0.06 0.06 {height}</size></box>
          </geometry>
          <material>
            <ambient>{black}</ambient>
            <diffuse>{black}</diffuse>
          </material>
        </visual>

        <collision name="collision">
          <pose>0 0 {height/2} 0 0 0</pose>
          <geometry>
            <box><size>{length} {depth} {height}</size></box>
          </geometry>
        </collision>
      </link>
    </model>
"""


def pallet_stack(name, x, y, box_count=4):
    result = ""
    # pallet base
    result += simple_box_model(
        f"{name}_pallet",
        x, y, 0.07,
        0.9, 0.7, 0.14,
        color="0.45 0.28 0.08 1"
    )

    coords = [(-0.18, -0.12), (0.18, -0.12), (-0.18, 0.12), (0.18, 0.12)]
    for i in range(min(box_count, len(coords))):
        dx, dy = coords[i]
        result += simple_box_model(
            f"{name}_box_{i}",
            x + dx, y + dy, 0.24,
            0.28, 0.22, 0.18,
            color="0.73 0.58 0.34 1"
        )
    return result


def world():
    text = """<?xml version="1.0" ?>
<sdf version="1.6">
  <world name="fuel_warehouse_world">

    <physics type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_update_rate>1000</real_time_update_rate>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <gravity>0 0 -9.8</gravity>

    <scene>
      <ambient>0.85 0.85 0.85 1</ambient>
      <background>0.7 0.7 0.7 1</background>
      <shadows>true</shadows>
    </scene>

    <include>
      <uri>model://sun</uri>
    </include>

    <include>
      <uri>model://Warehouse</uri>
      <pose>0 0 0 0 0 0</pose>
    </include>
"""

    # =========================
    # BIG SHELVES AROUND SIDES
    # =========================

    # Left wall shelves
    left_racks = [
        ("left_rack_top",   -5.2,  2.7, 1.5708, 4.4),
        ("left_rack_bottom",-5.2, -2.7, 1.5708, 4.4),
    ]

    # Right side shelves (3 long rows like the reference)
    right_racks = [
        ("right_rack_top",    3.2,  2.7, 0.0, 4.8),
        ("right_rack_middle", 3.2,  0.0, 0.0, 4.8),
        ("right_rack_bottom", 3.2, -2.7, 0.0, 4.8),
    ]

    # Bottom shelves
    bottom_racks = [
        ("bottom_left",  -1.7, -4.6, 0.0, 3.6),
        ("bottom_right",  2.2, -4.6, 0.0, 3.6),
    ]

    all_big_racks = left_racks + right_racks + bottom_racks

    for name, x, y, yaw, length in all_big_racks:
        text += rack_model(name, x, y, yaw=yaw, length=length, depth=0.7)
        text += boxes_on_rack(name, x, y, yaw, rack_length=length)

    # ====================================
    # LOW STORAGE RACKS IN THE CENTER AREA
    # ====================================

    # Keep center OPEN, only use low pallet racks
    center_low_racks = [
        (-1.2,  1.2), (0.4,  1.2), (2.0,  1.2),
        (-1.2,  0.0), (0.4,  0.0), (2.0,  0.0),
        (-1.2, -1.2), (0.4, -1.2), (2.0, -1.2),
    ]

    for i, (x, y) in enumerate(center_low_racks):
        text += low_center_rack(f"center_low_rack_{i}", x, y, yaw=0.0, length=1.3, depth=0.45, height=0.38)
        # a few small boxes on top
        text += simple_box_model(f"center_low_box_{i}_a", x - 0.2, y, 0.52, 0.22, 0.18, 0.16, "0.75 0.60 0.35 1")
        text += simple_box_model(f"center_low_box_{i}_b", x + 0.2, y, 0.52, 0.22, 0.18, 0.16, "0.75 0.60 0.35 1")

    # ====================
    # LOOSE PALLET GROUPS
    # ====================

    # Small loose groups, not giant stacks in the middle
    pallet_groups = [
        (-2.2,  0.6, 4),
        (-2.0, -0.2, 3),
        ( 1.1, -3.0, 4),
        ( 1.9, -3.0, 4),
        ( 2.7, -2.9, 3),
    ]

    for i, (x, y, n) in enumerate(pallet_groups):
        text += pallet_stack(f"pallet_group_{i}", x, y, n)

    # ====================
    # DROP / PICKUP ZONES
    # ====================

    text += marker_box("pickup_zone",  -4.0,  1.0, 0.01, 1.2, 1.2, 0.02, "0 1 0 0.45")
    text += marker_box("pickup_zone2", -4.0, -1.8, 0.01, 1.2, 1.2, 0.02, "0 1 0 0.45")
    text += marker_box("drop_zone1",    4.6,  1.2, 0.01, 1.2, 1.2, 0.02, "0 1 0 0.45")
    text += marker_box("drop_zone2",    4.6, -1.8, 0.01, 1.2, 1.2, 0.02, "0 1 0 0.45")

    text += """
  </world>
</sdf>
"""
    return text


if __name__ == "__main__":
    OUT.write_text(world())
    print(f"Wrote {OUT}")