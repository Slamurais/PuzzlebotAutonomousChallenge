FROM osrf/ros:humble-desktop

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    nano \
    ros-humble-foxglove-bridge \
    ros-humble-v4l2-camera \
    tmux \
    lsb-release \
    gnupg \
    curl \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    mesa-utils \
    ros-humble-joint-state-publisher-gui \
    ros-humble-xacro \
    ros-humble-robot-state-publisher \
    ros-humble-rviz2 \
    && rm -rf /var/lib/apt/lists/*

# Add the Gazebo (Ignition Fortress) repository key and source list
RUN curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

# Install Gazebo Fortress and the ROS 2 Humble bridge
RUN apt-get update && apt-get install -y \
    ignition-fortress \
    ros-humble-ros-gz \
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