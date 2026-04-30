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

# Install Gazebo Fortress, ROS 2 bridge, and ROS 2 Control suite
RUN apt-get update && apt-get install -y \
    ignition-fortress \
    ros-humble-ros-gz \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-ign-ros2-control \
    && rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
RUN echo "source /root/PuzzlebotAutonomousChallenge/ros2_ws/install/setup.bash" >> ~/.bashrc

# ==============================================================================
# When adding new dependencies, please leave a comment explaining which package 
# and node requires it. This helps trace dependencies and keep the image clean.
# Format: # Necessary for <package_name>/<node_name> node
# ==============================================================================

# Necessary for puzzlebot_control/pid_differential_pose_controller
# NOTE: This installs the ROS wrapper, but unfortunately pulls a broken, outdated 
# python3-transforms3d apt package with it. We override it with pip below.
RUN apt-get update && apt-get install -y \
    ros-humble-tf-transformations \
    && rm -rf /var/lib/apt/lists/*

# Necessary for puzzlebot_perception/object_detection_yolo node AND puzzlebot_control
# Note 1: numpy is pinned to <2.0.0 because ROS 2 Humble cv_bridge crashes with numpy 2.x
# Note 2: transforms3d is installed via pip here to gracefully OVERRIDE the broken apt version.
RUN pip3 install "numpy<2.0.0" ultralytics transforms3d

# Necessary for puzzlebot_control/joystick_teleop node
RUN apt-get update && apt-get install -y \
    ros-humble-joy \
    ros-humble-joy-teleop \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root/PuzzlebotAutonomousChallenge/ros2_ws

CMD ["bash"]