import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.descriptions import ParameterValue

def generate_launch_description():
    pkg_share = get_package_share_directory('my_first_bot')
    xacro_file = os.path.join(pkg_share, 'urdf', 'my_bot.urdf.xacro')
    
    # กำหนดที่อยู่ของไฟล์แผนที่
    world_file = os.path.join(pkg_share, 'worlds', 'my_map.world')

    robot_desc = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    # set_gl = SetEnvironmentVariable('LIBGL_ALWAYS_SOFTWARE', '1')
    set_wl = SetEnvironmentVariable('WAYLAND_DISPLAY', '')

    # แทรกตัวแปร world_file ลงไปหลังคำว่า '--verbose'
    gazebo_process = ExecuteProcess(
        cmd=['gazebo', '--verbose', world_file, '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so'],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_desc}]
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'my_robot'],
        output='screen'
    )


    return LaunchDescription([
        set_wl,
        gazebo_process,
        robot_state_publisher,
        spawn_entity,
    ])