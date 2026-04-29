import os
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():
    run_webcam_arg = DeclareLaunchArgument('webcam', default_value='false', description='Run host webcam')

    pkg_perception = get_package_share_directory('puzzlebot_perception')
    shared_param_file = os.path.join(pkg_perception, 'config', 'object_detection_yolo.yaml')

    v4l2_camera_node = Node(
        condition=IfCondition(LaunchConfiguration('webcam')),
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name='v4l2_camera_node',
        parameters=[shared_param_file]
    )

    object_detection_yolo = Node(
        package='puzzlebot_perception',
        executable='object_detection_yolo.py',
        name='object_detection_yolo',
        parameters=[shared_param_file]
    )

    foxglove_bridge = Node(
        package='foxglove_bridge',
        executable='foxglove_bridge',
        name='foxglove_bridge',
        parameters=[shared_param_file]
    )

    return LaunchDescription([
        run_webcam_arg,
        v4l2_camera_node,
        object_detection_yolo,
        foxglove_bridge,
    ])