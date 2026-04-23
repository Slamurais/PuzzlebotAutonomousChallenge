import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.conditions import IfCondition

def generate_launch_description():
    # Paths for dynamic layout resolution
    pkg_bringup = get_package_share_directory('puzzlebot_bringup')
    layout_path = os.path.join(pkg_bringup, 'foxglove_layouts', 'perception__object_detection_yolo.json')

    # Arguments
    run_sim_camera_arg = DeclareLaunchArgument('sim', default_value='false', description='Run host webcam')

    # 1. Camera Node (Using v4l2_camera)
    camera_node = Node(
        condition=IfCondition(LaunchConfiguration('sim')),
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name='puzzlebot_camera',
        remappings=[('/image_raw', '/camera/image_raw')],
        parameters=[{'video_device': '/dev/video0'}]
    )

    # 2. YOLO Object Detection Node (Calling from perception package)
    yolo_node = Node(
        package='puzzlebot_perception',
        executable='object_detection_yolo.py',
        name='yolo_detector',
        parameters=[{
            'model_name': 'yolo26n.pt',
            'image_topic': '/camera/image_raw',
            'conf_thresh': 0.5
        }]
    )

    # 3. Foxglove Bridge
    foxglove_bridge = Node(
        package='foxglove_bridge',
        executable='foxglove_bridge',
        name='foxglove_bridge',
        parameters=[{'port': 8765}]
    )

    log_layout = LogInfo(msg=f"\n\nFOXGLOVE LAYOUT: {layout_path}\n")

    return LaunchDescription([
        run_sim_camera_arg,
        camera_node,
        yolo_node,
        foxglove_bridge,
        log_layout
    ])