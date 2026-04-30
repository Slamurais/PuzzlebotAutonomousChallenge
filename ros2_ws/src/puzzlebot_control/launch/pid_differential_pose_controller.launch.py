import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    
    pkg_control = get_package_share_directory('puzzlebot_control')
    config_file = os.path.join(pkg_control, 'config', 'pid_differential_pose_controller.yaml')

    sim_is_true_arg = DeclareLaunchArgument(
        'sim_is_true',
        default_value='false',
        description='If true, avoids starting the custom odometry node'
    )

    odometry_node = Node(
        package='puzzlebot_control',
        executable='odometry.py', 
        name='odometry',     
        output='screen',
        parameters=[config_file],
        condition=UnlessCondition(LaunchConfiguration('sim_is_true'))
    )

    pid_differential_pose_controller_node = Node(
        package='puzzlebot_control',
        executable='pid_differential_pose_controller.py', 
        name='pid_differential_pose_controller', 
        output='screen',
        parameters=[config_file]     
    )

    return LaunchDescription([
        sim_is_true_arg,
        odometry_node,
        pid_differential_pose_controller_node
    ])