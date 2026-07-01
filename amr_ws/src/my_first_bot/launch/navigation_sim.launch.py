import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    my_bot_dir = get_package_share_directory('my_first_bot')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # 1. ไฟล์แผนที่ของคุณ (ดึงมาจากโฟลเดอร์ map อัตโนมัติ)
    map_file = os.path.join(my_bot_dir, 'map', 'my_warehouse_map.yaml')

    # 2. ดึงไฟล์เปิด Gazebo และหุ่นยนต์ (เปลี่ยนชื่อ sim.launch.py ให้ตรงกับของคุณ)
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(my_bot_dir, 'launch', 'sim.launch.py'))
    )

    # 3. เปิด Nav2 พร้อมโยนไฟล์แผนที่เข้าไป
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
        launch_arguments={
            'map': map_file,
            'use_sim_time': 'true'
        }.items()
    )

    # 4. เปิด RViz2 (พร้อมตั้งค่าหน้าจอให้เหมาะกับ Nav2 อัตโนมัติ)
    rviz_config_dir = os.path.join(nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_dir],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    return LaunchDescription([
        sim_launch,
        nav2_launch,
        rviz_node
    ])