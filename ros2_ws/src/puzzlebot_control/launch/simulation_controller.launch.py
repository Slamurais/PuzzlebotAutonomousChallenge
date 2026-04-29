from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
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

    return LaunchDescription([
        joint_state_spawner,
        diff_drive_spawner
    ])