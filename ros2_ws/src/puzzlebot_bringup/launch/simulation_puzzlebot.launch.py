import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

def generate_launch_description():
    pkg_description = get_package_share_directory('puzzlebot_description')
    pkg_control = get_package_share_directory('puzzlebot_control')
    rviz_config_file = os.path.join(pkg_description, 'rviz_config', 'simulation_gazebo.rviz')

    simulation_gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_description, 'launch', 'simulation_gazebo.launch.py'))
    )

    simulation_controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_control, 'launch', 'simulation_controller.launch.py'))
    )

    joystick_teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_control, 'launch', 'joystick_teleop.launch.py')),
        launch_arguments={'use_sim_time': 'True'}.items()
    )

    pid_differential_pose_controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_control, 'launch', 'pid_differential_pose_controller.launch.py')),
        launch_arguments={'sim_is_true': 'true'}.items()
    )

    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        output='screen',
        remappings=[('/cmd_vel_out', '/cmd_vel')],
        parameters=[os.path.join(pkg_control, 'config', 'twist_mux.yaml')]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        simulation_gazebo_launch,
        simulation_controller_launch,
        joystick_teleop_launch,  
        pid_differential_pose_controller_launch,
        twist_mux_node,
        rviz_node
    ])