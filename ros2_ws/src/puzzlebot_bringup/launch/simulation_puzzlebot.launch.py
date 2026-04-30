import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_desc = get_package_share_directory('puzzlebot_description')
    pkg_control = get_package_share_directory('puzzlebot_control')
    rviz_config_file = os.path.join(pkg_desc, 'rviz_config', 'simulation_gazebo.rviz')

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_desc, 'launch', 'simulation_gazebo.launch.py'))
    )

    simulation_controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_control, 'launch', 'simulation_controller.launch.py'))
    )

    joystick_teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_control, 'launch', 'joystick_teleop.launch.py')),
        launch_arguments={'use_sim_time': 'True'}.items()
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': True}]
    )

    ros_gz_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/image_raw"],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        gazebo_launch,
        simulation_controller_launch,
        joystick_teleop_launch,  
        rviz_node,
        ros_gz_image_bridge
    ])