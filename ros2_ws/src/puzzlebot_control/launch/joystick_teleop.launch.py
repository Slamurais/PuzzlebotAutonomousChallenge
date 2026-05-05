import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_control = get_package_share_directory('puzzlebot_control')

    use_sim_time_arg = DeclareLaunchArgument(
        name='use_sim_time', 
        default_value='False',
        description='Use simulated time'
    )

    config_file = os.path.join(pkg_control, 'config', 'joystick_teleop.yaml')

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joystick',
        parameters=[
            config_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    joy_teleop_node = Node(
        package='joy_teleop',
        executable='joy_teleop',
        name='joy_teleop',
        parameters=[
            config_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    return LaunchDescription([
        use_sim_time_arg,
        joy_node,
        joy_teleop_node
    ])