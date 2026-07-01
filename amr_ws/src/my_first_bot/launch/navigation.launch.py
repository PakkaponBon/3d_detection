import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node


def generate_launch_description():
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    my_first_bot_dir = get_package_share_directory('my_first_bot')

    map_file = '/home/bo/amr_ws/my_warehouse_map_new1.yaml'
    nav2_params_file = '/home/bo/amr_ws/src/my_first_bot/config/nav2_params.yaml'

    rviz_config_file = os.path.join(
        my_first_bot_dir,
        'rviz',
        'nav2_auto.rviz'
    )

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_file,
            'params_file': nav2_params_file,
            'use_sim_time': 'true',
            'autostart': 'true',
        }.items()
    )

    pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        output='screen',
        remappings=[
            ('cloud_in', '/points'),
            ('scan', '/scan'),
        ],
        parameters=[{
            'target_frame': 'lidar_link',
            'use_sim_time': True,

            # 3D lidar height slice converted into /scan
            # Good for warehouse racks, walls, boxes, and pallets
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

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_nav',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{
            'use_sim_time': True
        }]
    )

    return LaunchDescription([
        nav2_launch,
        pointcloud_to_laserscan_node,
        rviz_node,
    ])