# 3D Detection AMR POC

This repository contains my ROS 2 AMR simulation and LiDAR-based 3D person detection proof of concept.

## Project Goal

The goal is to move from an AGV-style robot concept toward an AMR by adding:

- Mapping
- Navigation
- 3D LiDAR perception
- AI person detection

## System

The project uses:

- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Classic
- Nav2
- RViz2
- OpenPCDet
- PointPillars

## Repository Structure

3d_detection/
- amr_ws/
  - src/my_first_bot/
  - maps/
  - nav_config/
  - my_warehouse_map_new1.yaml
  - my_warehouse_map_new1.pgm
- .gitignore
- README.md

## Current Status

Completed:

- Gazebo AMR simulation
- 3D LiDAR point cloud
- 2D map creation
- Nav2 navigation
- CVAT 3D labeling workflow
- PointPillars training
- Live person detection in RViz

## AI Detection Workflow

Gazebo LiDAR point cloud
-> ROS 2 bag recording
-> PCD export
-> CVAT 3D annotation
-> OpenPCDet dataset conversion
-> PointPillars training
-> Live ROS 2 detection in RViz

## Not Included

Large generated files are not uploaded to GitHub:

- build/
- install/
- log/
- ROS bags
- PCD datasets
- OpenPCDet checkpoints
- RTAB-Map .db files
- Python virtual environments

## Basic Run

After cloning on a new PC:

1. Go to the workspace:

cd ~/github/3d_detection/amr_ws

2. Build:

colcon build

3. Source workspace:

source install/setup.bash

4. Run simulation:

ros2 launch my_first_bot full_sim.launch.py

## Note

This project is a proof of concept, not a production safety system.
