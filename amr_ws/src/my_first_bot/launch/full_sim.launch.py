import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node

def generate_launch_description():
    urdf_path = '/home/bo/amr_ws/src/my_first_bot/urdf/my_bot.urdf'
    ekf_path  = '/home/bo/amr_ws/ekf.yaml'

    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    return LaunchDescription([

        # Gazebo
        ExecuteProcess(
            cmd=[
                'gazebo', '--verbose',
                '-s', 'libgazebo_ros_init.so',
                '-s', 'libgazebo_ros_factory.so',
                '/home/bo/amr_ws/src/my_first_bot/worlds/newwarehouse.world'
            ],
            cwd='/home/bo/amr_ws/src/aws-robomaker-small-warehouse-world',
            output='screen'
        ),

        # Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': robot_desc,
                'use_sim_time': True,
            }],
            output='screen'
        ),

        # Spawn Robot
        TimerAction(
            period=3.0,
            actions=[
                Node(
                    package='gazebo_ros',
                    executable='spawn_entity.py',
                    arguments=[
                        '-entity', 'my_robot',
                        '-file', urdf_path,
                        '-x', '0.0',
                        '-y', '0.0',
                        '-z', '0.1',
                        '-Y', '0.0'
                    ],
                    output='screen'
                )
            ]
        ),

        # EKF
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_path, {'use_sim_time': True}]
        ),
    ])