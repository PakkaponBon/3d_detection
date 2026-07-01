import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.descriptions import ParameterValue

def generate_launch_description():
    pkg_share = get_package_share_directory('my_first_bot')
    xacro_file = os.path.join(pkg_share, 'urdf', 'my_bot.urdf.xacro')
    robot_desc = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_desc}]
        ),
        # 🌟 นี่คือพระเอกขี่ม้าขาวที่เพิ่มเข้ามา! (ตัวบอกองศาข้อต่อ)
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui'
        ),
        Node(
            package='rviz2',
            executable='rviz2'
        )
    ])