#!/usr/bin/env python3

import math
import numpy as np
from scipy.spatial import cKDTree

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2

from visualization_msgs.msg import Marker, MarkerArray


class Live3DDetector(Node):
    def __init__(self):
        super().__init__('live_3d_detector')

        self.declare_parameter('cloud_topic', '/points')
        self.declare_parameter('marker_topic', '/detected_object_markers')

        self.declare_parameter('min_x', 0.35)
        self.declare_parameter('max_x', 5.0)
        self.declare_parameter('min_y', -1.6)
        self.declare_parameter('max_y', 1.6)
        self.declare_parameter('min_z', -0.40)
        self.declare_parameter('max_z', 1.60)

        self.declare_parameter('min_range', 0.45)
        self.declare_parameter('max_range', 6.0)

        self.declare_parameter('voxel_size', 0.08)
        self.declare_parameter('cluster_tolerance', 0.28)
        self.declare_parameter('min_cluster_points', 10)
        self.declare_parameter('max_cluster_points', 4000)

        self.cloud_topic = self.get_parameter('cloud_topic').value
        self.marker_topic = self.get_parameter('marker_topic').value

        self.sub = self.create_subscription(
            PointCloud2,
            self.cloud_topic,
            self.cloud_callback,
            10
        )

        self.marker_pub = self.create_publisher(
            MarkerArray,
            self.marker_topic,
            10
        )

        self.get_logger().info('Live 3D detector started')
        self.get_logger().info(f'Subscribing to: {self.cloud_topic}')
        self.get_logger().info(f'Publishing markers to: {self.marker_topic}')

    def cloud_callback(self, msg):
        min_x = self.get_parameter('min_x').value
        max_x = self.get_parameter('max_x').value
        min_y = self.get_parameter('min_y').value
        max_y = self.get_parameter('max_y').value
        min_z = self.get_parameter('min_z').value
        max_z = self.get_parameter('max_z').value

        min_range = self.get_parameter('min_range').value
        max_range = self.get_parameter('max_range').value

        points = []

        for p in point_cloud2.read_points(
            msg,
            field_names=('x', 'y', 'z'),
            skip_nans=True
        ):
            x = float(p[0])
            y = float(p[1])
            z = float(p[2])

            # Local detection box in lidar frame.
            # x = forward, y = left/right, z = up/down relative to lidar_link.
            if x < min_x or x > max_x:
                continue

            if y < min_y or y > max_y:
                continue

            if z < min_z or z > max_z:
                continue

            dist = math.sqrt(x * x + y * y + z * z)

            if dist < min_range:
                continue

            if dist > max_range:
                continue

            points.append([x, y, z])

        if len(points) < 20:
            self.publish_markers([], msg.header)
            return

        pts = np.array(points, dtype=np.float32)

        voxel_size = self.get_parameter('voxel_size').value
        pts = self.voxel_downsample(pts, voxel_size)

        if len(pts) < 20:
            self.publish_markers([], msg.header)
            return

        clusters = self.euclidean_clusters(
            pts,
            tolerance=self.get_parameter('cluster_tolerance').value,
            min_points=self.get_parameter('min_cluster_points').value,
            max_points=self.get_parameter('max_cluster_points').value
        )

        detections = []

        for cluster_indices in clusters:
            cluster = pts[cluster_indices]

            min_xyz = cluster.min(axis=0)
            max_xyz = cluster.max(axis=0)

            center = (min_xyz + max_xyz) / 2.0
            size = max_xyz - min_xyz

            sx = float(size[0])
            sy = float(size[1])
            sz = float(size[2])

            # Reject very tiny noise.
            if sx < 0.08 and sy < 0.08 and sz < 0.08:
                continue

            # Reject flat floor-like clusters.
            if sz < 0.06:
                continue

            # Reject very huge structures like long walls/shelves.
            if sx > 2.5 or sy > 2.5 or sz > 2.0:
                continue

            # Reject long thin wall-like lines.
            if sx > 1.8 and sy < 0.12:
                continue

            if sy > 1.8 and sx < 0.12:
                continue

            detections.append((center, size))

        self.publish_markers(detections, msg.header)

        if detections:
            self.get_logger().info(f'Detected {len(detections)} object(s)')

    def voxel_downsample(self, pts, voxel_size):
        if len(pts) == 0:
            return pts

        keys = np.floor(pts / voxel_size).astype(np.int32)

        voxel_dict = {}
        for i, key in enumerate(map(tuple, keys)):
            if key not in voxel_dict:
                voxel_dict[key] = pts[i]

        return np.array(list(voxel_dict.values()), dtype=np.float32)

    def euclidean_clusters(self, pts, tolerance, min_points, max_points):
        tree = cKDTree(pts)
        n = len(pts)

        visited = np.zeros(n, dtype=bool)
        clusters = []

        for i in range(n):
            if visited[i]:
                continue

            queue = [i]
            visited[i] = True
            cluster = []

            while queue:
                idx = queue.pop()
                cluster.append(idx)

                neighbors = tree.query_ball_point(pts[idx], tolerance)

                for nb in neighbors:
                    if not visited[nb]:
                        visited[nb] = True
                        queue.append(nb)

            if min_points <= len(cluster) <= max_points:
                clusters.append(cluster)

        return clusters

    def publish_markers(self, detections, header):
        marker_array = MarkerArray()

        clear_marker = Marker()
        clear_marker.header = header
        clear_marker.action = Marker.DELETEALL
        marker_array.markers.append(clear_marker)

        for i, (center, size) in enumerate(detections):
            marker = Marker()
            marker.header = header
            marker.ns = 'detected_3d_objects'
            marker.id = i
            marker.type = Marker.CUBE
            marker.action = Marker.ADD

            marker.pose.position.x = float(center[0])
            marker.pose.position.y = float(center[1])
            marker.pose.position.z = float(center[2])
            marker.pose.orientation.w = 1.0

            marker.scale.x = max(float(size[0]), 0.08)
            marker.scale.y = max(float(size[1]), 0.08)
            marker.scale.z = max(float(size[2]), 0.08)

            marker.color.r = 1.0
            marker.color.g = 0.45
            marker.color.b = 0.0
            marker.color.a = 0.45

            marker.lifetime.sec = 1

            marker_array.markers.append(marker)

        self.marker_pub.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)

    node = Live3DDetector()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()