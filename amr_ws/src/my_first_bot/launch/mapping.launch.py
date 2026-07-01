import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time'
    )

    # Convert 3D lidar point cloud /points into 2D laser scan /scan for SLAM
    pointcloud_to_laserscan = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        output='screen',
        remappings=[
            ('cloud_in', '/points'),
            ('scan', '/scan'),
        ],
        parameters=[{
            'use_sim_time': use_sim_time,
            'target_frame': 'lidar_link',

            # Use useful lower warehouse obstacle slice
            # Sees rack legs, pallets, boxes, walls
            'min_height': 0.10,
            'max_height': 0.50,

            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.0087,
            'scan_time': 0.1,
            'range_min': 0.4,
            'range_max': 12.0,

            'use_inf': True,
            'inf_epsilon': 1.0,
        }]
    )

    # SLAM Toolbox online async mapping
    slam_toolbox = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,

            # Frames
            'odom_frame': 'odom',
            'map_frame': 'map',
            'base_frame': 'base_footprint',
            'scan_topic': '/scan',

            # Mapping behavior
            'mode': 'mapping',
            'debug_logging': False,
            'throttle_scans': 1,
            'transform_publish_period': 0.02,
            'map_update_interval': 1.0,
            'resolution': 0.05,
            'max_laser_range': 12.0,
            'minimum_time_interval': 0.1,
            'transform_timeout': 0.2,
            'tf_buffer_duration': 30.0,
            'stack_size_to_use': 40000000,

            # Scan matcher tuning
            'use_scan_matching': True,
            'use_scan_barycenter': True,
            'minimum_travel_distance': 0.10,
            'minimum_travel_heading': 0.10,
            'scan_buffer_size': 10,
            'scan_buffer_maximum_scan_distance': 10.0,
            'link_match_minimum_response_fine': 0.1,
            'link_scan_maximum_distance': 1.5,
            'loop_search_maximum_distance': 3.0,
            'do_loop_closing': True,
            'loop_match_minimum_chain_size': 10,
            'loop_match_maximum_variance_coarse': 3.0,
            'loop_match_minimum_response_coarse': 0.35,
            'loop_match_minimum_response_fine': 0.45,

            # Correlation search
            'correlation_search_space_dimension': 0.5,
            'correlation_search_space_resolution': 0.01,
            'correlation_search_space_smear_deviation': 0.1,

            # Loop closure search
            'loop_search_space_dimension': 8.0,
            'loop_search_space_resolution': 0.05,
            'loop_search_space_smear_deviation': 0.03,

            # Scan matcher search
            'distance_variance_penalty': 0.5,
            'angle_variance_penalty': 1.0,
            'fine_search_angle_offset': 0.00349,
            'coarse_search_angle_offset': 0.349,
            'coarse_angle_resolution': 0.0349,
            'minimum_angle_penalty': 0.9,
            'minimum_distance_penalty': 0.5,
            'use_response_expansion': True,
        }]
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_mapping',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )

    return LaunchDescription([
        use_sim_time_arg,
        pointcloud_to_laserscan,
        slam_toolbox,
        rviz,
    ])