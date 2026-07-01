import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_my_bot = FindPackageShare('my_first_bot')
    pkg_gazebo_ros = FindPackageShare('gazebo_ros')
    
    # Path to xacro
    xacro_file = PathJoinSubstitution([pkg_my_bot, 'urdf', 'my_bot.urdf.xacro'])
    
    # Absolute path to world file
    world_path = os.path.expanduser(
        '~/amr_ws/src/aws-robomaker-small-warehouse-world/worlds/no_roof_small_warehouse/no_roof_small_warehouse.world'
    )
    
    # Set model path and locale (C-locale math fix for meshes)
    os.environ['GAZEBO_MODEL_PATH'] = os.path.expanduser('~/amr_ws/src/aws-robomaker-small-warehouse-world/models')
    os.environ['LC_NUMERIC'] = 'C'

    # 1. Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'use_sim_time': True,
            'robot_description': Command(['xacro ', xacro_file])
        }]
    )

    # 2. Official Gazebo ROS Launch Wrapper (Handles all plugin dependencies properly)
    gazebo_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_gazebo_ros, 'launch', 'gazebo.launch.py'])
        ),
        launch_arguments={
            'world': world_path,
            'verbose': 'true'
        }.items()
    )

    # 3. Spawn Entity (Automatically waits for the factory plugin in the included launch)
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'my_robot',
            '-x', '0.0', '-y', '0.0', '-z', '0.1' # Rests correctly on the floor plane
        ],
        output='screen'
    )

    return LaunchDescription([
        robot_state_publisher,
        gazebo_sim,
        spawn_entity
    ])
