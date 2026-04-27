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
    puzzlebot_description_dir = get_package_share_directory('puzzlebot_description')
    ros_gz_sim_dir = get_package_share_directory('ros_gz_sim')

    urdf_file = os.path.join(puzzlebot_description_dir, 'urdf', 'puzzlebot.urdf.xacro')
    world_file = os.path.join(puzzlebot_description_dir, 'worlds', 'e80_factory.sdf')
    rviz_config_file = os.path.join(puzzlebot_description_dir, 'rviz_config', 'gazebo_simulation.rviz')

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

    model_path = str(Path(puzzlebot_description_dir).parent.resolve())
    ign_resource_path = SetEnvironmentVariable('IGN_GAZEBO_RESOURCE_PATH', model_path)

    gazebo = IncludeLaunchDescription(
            PythonLaunchDescriptionSource([os.path.join(ros_gz_sim_dir, 'launch', 'gz_sim.launch.py')]),
            launch_arguments=[
                ('gz_args', [' -v 4', ' -r ', world_file])
            ]
        )
    
    gz_spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'puzzlebot'
        ],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            '/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan'
        ],
        output='screen'
    )

    joint_state_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
    )

    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_controller"],
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
        model_arg,
        robot_state_publisher_node,
        ign_resource_path,
        gazebo,
        gz_spawn_entity,
        bridge,
        joint_state_spawner,
        diff_drive_spawner,
        rviz_node
    ])