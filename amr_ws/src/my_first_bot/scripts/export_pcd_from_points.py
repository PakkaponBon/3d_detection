#!/usr/bin/env python3

import os
import numpy as np

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2


class PCDExporter(Node):
    def __init__(self):
        super().__init__('pcd_exporter')

        self.declare_parameter('topic', '/points')
        self.declare_parameter('output_dir', '/home/bo/amr_ws/datasets/pcd_export/warehouse_3d_run_01')
        self.declare_parameter('every_n', 5)
        self.declare_parameter('max_frames', 300)

        self.topic = self.get_parameter('topic').value
        self.output_dir = self.get_parameter('output_dir').value
        self.every_n = int(self.get_parameter('every_n').value)
        self.max_frames = int(self.get_parameter('max_frames').value)

        os.makedirs(self.output_dir, exist_ok=True)

        self.msg_count = 0
        self.saved_count = 0

        self.sub = self.create_subscription(
            PointCloud2,
            self.topic,
            self.cloud_callback,
            10
        )

        self.get_logger().info(f'Listening to {self.topic}')
        self.get_logger().info(f'Saving to {self.output_dir}')
        self.get_logger().info(f'Every {self.every_n} clouds, max {self.max_frames} frames')

    def cloud_callback(self, msg):
        self.msg_count += 1

        if self.msg_count % self.every_n != 0:
            return

        if self.saved_count >= self.max_frames:
            return

        points = []

        for p in point_cloud2.read_points(
            msg,
            field_names=('x', 'y', 'z', 'intensity'),
            skip_nans=True
        ):
            try:
                # Works when read_points returns structured/named fields
                x = float(p['x'])
                y = float(p['y'])
                z = float(p['z'])
                intensity = float(p['intensity'])
            except Exception:
                # Works when read_points returns tuple/list style
                x = float(p[0])
                y = float(p[1])
                z = float(p[2])
                intensity = float(p[3])

            if abs(x) > 100 or abs(y) > 100 or abs(z) > 100:
                continue

            points.append([x, y, z, intensity])

        if len(points) < 10:
            return

        points_np = np.array(points, dtype=np.float32)
        self.get_logger().info(
            f'Intensity min={points_np[:,3].min():.5f}, max={points_np[:,3].max():.5f}'
        )

        filename = os.path.join(
            self.output_dir,
            f'frame_{self.saved_count:06d}.pcd'
        )

        self.write_pcd_ascii(filename, points_np)

        self.get_logger().info(
            f'Saved {filename} with {len(points_np)} points'
        )

        self.saved_count += 1

    def write_pcd_ascii(self, filename, points):
        n = points.shape[0]

        header = (
            '# .PCD v0.7 - Point Cloud Data file format\n'
            'VERSION 0.7\n'
            'FIELDS x y z intensity\n'
            'SIZE 4 4 4 4\n'
            'TYPE F F F F\n'
            'COUNT 1 1 1 1\n'
            f'WIDTH {n}\n'
            'HEIGHT 1\n'
            'VIEWPOINT 0 0 0 1 0 0 0\n'
            f'POINTS {n}\n'
            'DATA ascii\n'
        )

        with open(filename, 'w') as f:
            f.write(header)
            for x, y, z, intentity in points:
                f.write(f'{x:.5f} {y:.5f} {z:.5f} {intentity:.5f}\n')


def main(args=None):
    rclpy.init(args=args)
    node = PCDExporter()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()