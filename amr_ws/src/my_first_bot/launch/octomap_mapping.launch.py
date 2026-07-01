from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    octomap_server = Node(
        package='octomap_server',
        executable='octomap_server_node',
        name='octomap_server',
        output='screen',
        parameters=[{
            'use_sim_time': True,

            # Frames
            'frame_id': 'map',
            'base_frame_id': 'base_footprint',

            # Input cloud
            'cloud_in': '/points',

            # Map resolution. Smaller = better detail, heavier CPU.
            'resolution': 0.10,

            # Sensor limits
            'sensor_model/max_range': 8.0,

            # Ignore ground / very low points
            'pointcloud_min_z': 0.05,
            'pointcloud_max_z': 3.0,

            # Keep map updated
            'latch': False,
        }],
        remappings=[
            ('cloud_in', '/points'),
        ]
    )

    return LaunchDescription([
        octomap_server
    ])