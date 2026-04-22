FROM osrf/ros:humble-desktop

RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    nano \
    && rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

WORKDIR /root/PuzzlebotAutonomousChallenge/ros2_ws

CMD ["bash"]
