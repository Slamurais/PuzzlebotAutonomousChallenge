import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_desc = get_package_share_directory('puzzlebot_description')
    pkg_control = get_package_share_directory('puzzlebot_control')

    # This automatically handles the URDF, Robot State Publisher, 
    # Joint State Publisher, and opens RViz2
    display_rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_desc, 'launch', 'display_rviz.launch.py')
        )
    )

    joystick_teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_control, 'launch', 'joystick_teleop.launch.py')
        ),
        launch_arguments={'use_sim_time': 'False'}.items()
    )

    odometry_pid_differential_pose_controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_control, 'launch', 'pid_differential_pose_controller.launch.py')
        ),
        launch_arguments={'sim_is_true': 'false'}.items()
    )

    twist_mux_node = Node(
        package='twist_mux',
        executable='twist_mux',
        output='screen',
        remappings=[('/cmd_vel_out', '/cmd_vel')],
        parameters=[os.path.join(pkg_control, 'config', 'twist_mux.yaml')]
    )

    return LaunchDescription([
        display_rviz_launch,
        odometry_pid_differential_pose_controller_launch,
        joystick_teleop_launch,
        twist_mux_node
    ])