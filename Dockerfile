FROM osrf/ros:humble-desktop

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    nano \
    ros-humble-foxglove-bridge \
    ros-humble-v4l2-camera \
    tmux \
    && rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
RUN echo "source /root/PuzzlebotAutonomousChallenge/ros2_ws/install/setup.bash" >> ~/.bashrc

# ==============================================================================
# When adding new dependencies, please leave a comment explaining which package 
# and node requires it. This helps trace dependencies and keep the image clean.
# Format: # Necessary for <package_name>/<node_name> node
# ==============================================================================

# Necessary for puzzlebot_perception/object_detection_yolo node
# Note: numpy is pinned to <2.0.0 because ROS 2 Humble cv_bridge crashes with numpy 2.x
RUN pip3 install "numpy<2.0.0" ultralytics

WORKDIR /root/PuzzlebotAutonomousChallenge/ros2_ws

CMD ["bash"]