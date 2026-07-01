from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Path to your existing warehouse launch file
    warehouse_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('aws_robomaker_small_warehouse_world'),
                'launch', 'no_roof_small_warehouse_launch.py'
            ])
        )
    )

    # Path to your existing robot spawn/navigation launch
    robot_navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('my_first_bot'),
                'launch', 'navigation.launch.py'
            ])
        )
    )

    return LaunchDescription([
        warehouse_launch,
        robot_navigation_launch
    ])