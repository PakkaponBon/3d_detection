# AI Workspace Notes

This folder contains custom AI files used for LiDAR-only 3D person detection.

The full OpenPCDet framework is not included in this repository. On a new PC, clone OpenPCDet separately and copy these custom files into it.

## Custom files

- OpenPCDet/tools/live_warehouse_detector_ros2.py
- OpenPCDet/tools/cfgs/custom_models/pointpillar_warehouse_person.yaml
- OpenPCDet/tools/cfgs/dataset_configs/custom_dataset_person.yaml
- converters/convert_gg6_person_to_openpcdet.py

## Workflow

1. Record ROS 2 point cloud data from /points
2. Export PCD frames
3. Label person cuboids in CVAT
4. Export CVAT Datumaro 3D data
5. Convert dataset to OpenPCDet format
6. Train PointPillars
7. Run live ROS 2 detector

## Not included

Large generated files are not stored in GitHub:

- Python virtual environment
- OpenPCDet build files
- OpenPCDet data/custom
- training datasets
- PCD files
- NPY files
- PKL info files
- model checkpoints

The trained checkpoint should be copied manually or stored separately.
