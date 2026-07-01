#!/usr/bin/env python3

import sys
import math
import logging
from pathlib import Path

import numpy as np
import torch

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2

from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point


# Make OpenPCDet importable
sys.path.append("/home/bo/ai_ws/OpenPCDet")

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets.dataset import DatasetTemplate
from pcdet.models import build_network, load_data_to_gpu


CFG_FILE = "/home/bo/ai_ws/OpenPCDet/tools/cfgs/custom_models/pointpillar_warehouse.yaml"
CKPT_FILE = "/home/bo/ai_ws/OpenPCDet/output/custom_models/pointpillar_warehouse/person_gg6/ckpt/checkpoint_epoch_50.pth"

POINT_TOPIC = "/points"
MARKER_TOPIC = "/ai_detections/boxes"

SCORE_THRESH = 0.30
MAX_BOXES = 10

# Process every Nth point cloud frame.
# If Gazebo/RViz gets slow, increase to 5 or 10.
PROCESS_EVERY_N_FRAMES = 3


class LiveDataset(DatasetTemplate):
    def __init__(self, dataset_cfg, class_names, logger):
        super().__init__(
            dataset_cfg=dataset_cfg,
            class_names=class_names,
            training=False,
            root_path=Path("/home/bo/ai_ws/OpenPCDet/data/custom"),
            logger=logger
        )

    def __len__(self):
        return 1

    def __getitem__(self, index):
        raise NotImplementedError

    def prepare_live_points(self, points):
        data_dict = {
            "points": points,
            "frame_id": "live"
        }
        return self.prepare_data(data_dict=data_dict)


def make_wire_box_marker(marker_id, frame_id, stamp, box, class_name, score):
    x, y, z, l, w, h, yaw = [float(v) for v in box]

    dx = l / 2.0
    dy = w / 2.0
    dz = h / 2.0

    corners = np.array([
        [ dx,  dy,  dz],
        [ dx, -dy,  dz],
        [-dx, -dy,  dz],
        [-dx,  dy,  dz],
        [ dx,  dy, -dz],
        [ dx, -dy, -dz],
        [-dx, -dy, -dz],
        [-dx,  dy, -dz],
    ], dtype=np.float32)

    R = np.array([
        [math.cos(yaw), -math.sin(yaw), 0.0],
        [math.sin(yaw),  math.cos(yaw), 0.0],
        [0.0,            0.0,           1.0],
    ], dtype=np.float32)

    corners = corners @ R.T + np.array([x, y, z], dtype=np.float32)

    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]

    marker = Marker()
    marker.header.frame_id = frame_id
    marker.header.stamp = stamp
    marker.ns = "ai_3d_boxes"
    marker.id = marker_id
    marker.type = Marker.LINE_LIST
    marker.action = Marker.ADD

    marker.scale.x = 0.04

    if class_name == "car":
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0
    else:
        marker.color.r = 1.0
        marker.color.g = 0.75
        marker.color.b = 0.0

    marker.color.a = 1.0

    for a, b in edges:
        pa = Point()
        pa.x = float(corners[a, 0])
        pa.y = float(corners[a, 1])
        pa.z = float(corners[a, 2])

        pb = Point()
        pb.x = float(corners[b, 0])
        pb.y = float(corners[b, 1])
        pb.z = float(corners[b, 2])

        marker.points.append(pa)
        marker.points.append(pb)

    return marker


def make_text_marker(marker_id, frame_id, stamp, box, class_name, score):
    x, y, z, l, w, h, yaw = [float(v) for v in box]

    marker = Marker()
    marker.header.frame_id = frame_id
    marker.header.stamp = stamp
    marker.ns = "ai_3d_labels"
    marker.id = marker_id
    marker.type = Marker.TEXT_VIEW_FACING
    marker.action = Marker.ADD

    marker.pose.position.x = x
    marker.pose.position.y = y
    marker.pose.position.z = z + h / 2.0 + 0.25

    marker.scale.z = 0.35

    marker.color.r = 1.0
    marker.color.g = 1.0
    marker.color.b = 1.0
    marker.color.a = 1.0

    marker.text = f"{class_name} {score:.2f}"

    return marker


class WarehouseDetectorNode(Node):
    def __init__(self):
        super().__init__("warehouse_3d_detector")

        self.pub = self.create_publisher(MarkerArray, MARKER_TOPIC, 10)
        self.sub = self.create_subscription(PointCloud2, POINT_TOPIC, self.points_callback, 10)

        self.frame_count = 0
        self.busy = False

        logging.basicConfig(level=logging.INFO)
        self.logger_py = logging.getLogger("warehouse_detector")

        self.get_logger().info("Loading OpenPCDet config...")
        cfg_from_yaml_file(CFG_FILE, cfg)

        self.class_names = cfg.CLASS_NAMES
        self.dataset = LiveDataset(cfg.DATA_CONFIG, self.class_names, self.logger_py)

        self.get_logger().info("Building PointPillars model...")
        self.model = build_network(
            model_cfg=cfg.MODEL,
            num_class=len(self.class_names),
            dataset=self.dataset
        )

        self.get_logger().info(f"Loading checkpoint: {CKPT_FILE}")
        self.model.load_params_from_file(
            filename=CKPT_FILE,
            logger=self.logger_py,
            to_cpu=False
        )

        self.model.cuda()
        self.model.eval()

        self.get_logger().info("Live 3D detector is ready.")
        self.get_logger().info(f"Subscribing: {POINT_TOPIC}")
        self.get_logger().info(f"Publishing: {MARKER_TOPIC}")

    def points_callback(self, msg):
        if self.busy:
            return

        self.frame_count += 1

        if self.frame_count % PROCESS_EVERY_N_FRAMES != 0:
            return

        self.busy = True

        try:
            pts = []

            for p in point_cloud2.read_points(
                msg,
                field_names=("x", "y", "z"),
                skip_nans=True
            ):
                x = float(p[0])
                y = float(p[1])
                z = float(p[2])

                if not math.isfinite(x) or not math.isfinite(y) or not math.isfinite(z):
                    continue

                pts.append([x, y, z, 0.0])

            if len(pts) < 100:
                self.busy = False
                return

            points = np.asarray(pts, dtype=np.float32)

            data_dict = self.dataset.prepare_live_points(points)
            batch_dict = self.dataset.collate_batch([data_dict])

            load_data_to_gpu(batch_dict)

            with torch.no_grad():
                pred_dicts, _ = self.model(batch_dict)

            pred = pred_dicts[0]

            pred_boxes = pred["pred_boxes"].detach().cpu().numpy()
            pred_scores = pred["pred_scores"].detach().cpu().numpy()
            pred_labels = pred["pred_labels"].detach().cpu().numpy()

            marker_array = MarkerArray()

            delete_marker = Marker()
            delete_marker.header.frame_id = msg.header.frame_id
            delete_marker.header.stamp = msg.header.stamp
            delete_marker.action = Marker.DELETEALL
            marker_array.markers.append(delete_marker)

            detections = []

            for box, score, label_id in zip(pred_boxes, pred_scores, pred_labels):
                score = float(score)

                if score < SCORE_THRESH:
                    continue

                if not np.all(np.isfinite(box)):
                    continue

                class_index = int(label_id) - 1

                if class_index < 0 or class_index >= len(self.class_names):
                    continue

                class_name = self.class_names[class_index]
                detections.append((score, class_name, box))

            detections = sorted(detections, key=lambda x: x[0], reverse=True)
            detections = detections[:MAX_BOXES]

            marker_id = 1

            for score, class_name, box in detections:
                marker_array.markers.append(
                    make_wire_box_marker(
                        marker_id,
                        msg.header.frame_id,
                        msg.header.stamp,
                        box,
                        class_name,
                        score
                    )
                )
                marker_id += 1

                marker_array.markers.append(
                    make_text_marker(
                        marker_id,
                        msg.header.frame_id,
                        msg.header.stamp,
                        box,
                        class_name,
                        score
                    )
                )
                marker_id += 1

            self.pub.publish(marker_array)

            self.get_logger().info(
                f"Detected {len(detections)} objects from {len(points)} points"
            )

        except Exception as e:
            self.get_logger().error(f"Inference failed: {repr(e)}")

        self.busy = False


def main():
    rclpy.init()
    node = WarehouseDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
