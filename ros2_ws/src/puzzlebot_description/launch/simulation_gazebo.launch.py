import os
from pathlib import Path
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, IncludeLaunchDescription
from launch.substitutions import Command, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_description = get_package_share_directory('puzzlebot_description')
    ros_gz_sim_dir = get_package_share_directory('ros_gz_sim')

    urdf_file = os.path.join(pkg_description, 'urdf', 'puzzlebot.urdf.xacro')
    world_file = os.path.join(pkg_description, 'worlds', 'e80_factory.sdf')
    
    gazebo_config_file = os.path.join(pkg_description, 'gazebo_config', 'simulation_gazebo.config')

    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=urdf_file,
        description='Absolute path to robot URDF file'
    )

    robot_description = ParameterValue(Command([
        'xacro ', LaunchConfiguration('model'), ' is_ignition:=true'
    ]), value_type=str)

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
    )

    model_path = str(Path(pkg_description).parent.resolve())
    ign_resource_path = SetEnvironmentVariable('IGN_GAZEBO_RESOURCE_PATH', model_path)

    gazebo_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(ros_gz_sim_dir, 'launch', 'gz_sim.launch.py')]),
            launch_arguments=[
                ('gz_args', [' -v 4', ' -r ', world_file, ' --gui-config ', gazebo_config_file])
            ]
        )
    
    gz_spawn_entity_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'puzzlebot'
        ],
        output='screen'
    )

    ros_gz_parameter_bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            '/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan'
        ],
        output='screen'
    )

    ros_gz_image_bridge_node = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/image_raw"],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        model_arg,
        robot_state_publisher_node,
        ign_resource_path,
        gazebo_launch,
        gz_spawn_entity_node,
        ros_gz_parameter_bridge_node,
        ros_gz_image_bridge_node
    ])