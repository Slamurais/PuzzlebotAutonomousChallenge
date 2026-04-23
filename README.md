# Puzzlebot Autonomous Challenge

<p align="justify">
Main project developed in collaboration with Manchester Robotics and E80 Group, as part of the undergraduate course <i>"Integration of Robotics and Intelligent Systems."</i>
</p>

<p align="justify">This repository provides the <strong>ROS 2 Humble workspace for Puzzlebot</strong>, an educational differential-drive mobile robot developed by Manchester Robotics.</p>

## Using Docker with Puzzlebot

<p align="justify">
This guide explains how to set up and manage the Puzzlebot development environment using Docker. This setup ensures a consistent ROS 2 Humble environment across different host systems.
</p>

### Prerequisites

<p align="justify">
This environment was developed and tested on <i>Ubuntu 24.04.4 LTS (Noble Numbat)</i>. Before proceeding, ensure you have <i>Docker</i> and the <i>Docker Compose</i> plugin installed.
</p>

#### Official Install Guides:

* *Docker*: https://docs.docker.com/engine/install/ubuntu/
* *Docker Compose*: https://docs.docker.com/compose/install/linux/

### Setting Up the Environment

<p align="justify">
Clone the repository and navigate to the root folder (that contains the <code>docker-compose.yml</code> file).
</p>

```bash
git clone https://github.com/Slamurais/PuzzlebotAutonomousChallenge.git
cd PuzzlebotAutonomousChallenge
```

### Building and Starting the Container

<p align="justify">
Build the Docker image using Docker Compose (this may take several minutes the first time) and start the container in detached mode to run it in the background.
</p>

```bash
docker compose up -d --build
```

### Accessing the Container

<p align="justify">
To open an interactive bash shell inside the running container, use the exec command:
</p>

```bash
docker compose exec puzzlebot_container bash
```

<p align="justify">
Your prompt will change to <code>root@...</code> indicating you are inside the container. Your default working directory is <code>/root/PuzzlebotAutonomousChallenge/ros2_ws</code>. When you are finished working inside the container and want to return to your host terminal type <code>exit</code> and press <code>Enter</code>.
</p>

### Working with ROS 2 Workspace

<p align="justify">
The entire <code>PuzzlebotAutonomousChallenge</code> folder from your host is mounted at <code>/root/PuzzlebotAutonomousChallenge</code>. Any changes made to the source files on your host are immediately visible inside the container, and vice versa.
</p>

#### Typical ROS 2 workflow inside the container:

* Source the ROS 2 environment (this was added to <code>~/.bashrc</code>, but can be done manually):

```bash
source /opt/ros/humble/setup.bash
```

* Build your workspace:

```bash
cd /root/PuzzlebotAutonomousChallenge/ros2_ws
colcon build --symlink-install
```

* Source the workspace overlay:

```bash
source install/setup.bash
```

* Run a launch file:

```bash
ros2 launch package launch_file.launch.py
```

### Managing the Container Lifecycle

<p align="justify">
Once your environment is set up, you can manage the state of the container using the following commands from the root of the repository.
</p>

#### Stopping and Starting

<p align="justify">
Use stop to pause the container without removing it. You can resume later with start.
</p>

```bash
docker compose stop
```

```bash
docker compose start
```

#### Deep Clean

<p align="justify">
This stops and deletes the container. This is recommended if you make changes to the <code>docker-compose.yml</code> or need to reset the environment completely.
</p>

```bash
docker compose down
```

#### Applying Configuration Changes Fast (No Rebuild)

<p align="justify">
If you make changes to the <code>docker-compose.yml</code> file but have <strong>not</strong> changed the <code>Dockerfile</code>, you do not need to wait for a full rebuild. Simply run:
</p>

```bash
docker compose up -d
```

## Project Structure

<p align="justify">
This repository is organized into modular ROS 2 packages.
</p>

```text
PuzzlebotAutonomousChallenge/ros2_ws/src/
├── puzzlebot_bringup/            
├── puzzlebot_msgs/               
├── puzzlebot_hardware/           
├── puzzlebot_perception/         
├── puzzlebot_navigation/         
└── puzzlebot_control/
```

#### Software Design Philosophy: The 5C Model

<p align="justify">
The architecture of this workspace follows the 5C model for component-based software design in robotics, ensuring that each package has a distinct and well-defined role in the system:
</p>

<ul>
  <li><p align="justify"><strong>Composition & Configuration (puzzlebot_bringup):</strong>  This package handles Composition by defining how various computations, communications, and coordinations are integrated into a single system. It also manages Configuration by centralizing the parameters that define the behavior of all components through launch files and parameter files.</p></li>
  <li><p align="justify"><strong>Communication (puzzlebot_msgs):</strong> This package is dedicated to Communication, defining the formal interfaces (messages, services, and actions) through which the results of computations are shared across the system.</p></li>
  <li><p align="justify"><strong>Computation & Coordination (Others):</strong>  The remaining packages—hardware, perception, navigation, and control—focus on Computation, which is the specific functionality or algorithm being executed, and Coordination, which determines when and how components change their behavior.</p></li>
</ul>

#### Autonomous Systems Pipeline

These packages follow the standard functional pipeline for autonomous systems:

<ul>
  <li><p align="justify"><strong>puzzlebot_hardware:</strong> This layer contains the drivers that ensure sensors can properly collect data about the environment. It conditions the raw data if needed before it enters the rest of the stack.</p></li>

  <li><p align="justify"><strong>puzzlebot_perception:</strong> This package interprets raw sensor data into a structured representation of the environment. It enables the robot to "see" and interpret the world, providing the situational awareness necessary for decision-making.</p></li>

  <li><p align="justify"><strong>puzzlebot_navigation:</strong> Using the world model from perception, navigation is the process of defining a safe and efficient path from a starting point to a goal. It relies heavily on maps and the current situational awareness to plan trajectories.</p></li>

  <li><p align="justify"><strong>puzzlebot_control:</strong> Finally, the control systems regulate the robot's actuators to follow the planned navigation trajectory. This layer is responsible for handling dynamic disturbances and ensuring the physical motors execute the path precisely.</p></li>
</ul>

## Package Descriptions

### puzzlebot_bringup

<p align="justify">
Its primary purpose is to provide centralized launch files that coordinate nodes from various packages, ensuring the robot system starts up with the correct parameters.
</p>

#### Use of Foxglove Studio UI

<p align="justify">
The <code>foxglove_layouts/</code> folder contains JSON configuration files for the Foxglove Studio UI.
</p>

<p align="justify">
To keep the system intuitive, layouts follow a 1:1 naming convention with their corresponding launch files. For example, <code>object_detection_yolo.launch.py</code> works specifically with <code>object_detection_yolo.json</code>.
</p>

<p align="justify">
To visualize your data, you must install Foxglove Studio directly on your host PC by downloading it from <a href="https://foxglove.dev/download" style="color: blue;">https://foxglove.dev/download</a>.
</p>

<p align="justify">
It is important to note that even though the UI is on your host, the launch file runs inside the Docker container and correctly establishes the connection.
</p>

<p align="justify">
The launch files in this package automatically execute the <code>foxglove_bridge</code> and execute the necessary commands to open the port, so you only need to worry about the UI part.
</p>

<p align="justify">
Once the launch is active, open your host app, select <code>Open Connection</code>, choose <code>Foxglove WebSocket</code>, and connect to <code>ws://localhost:8765</code>.
</p>

<p align="justify">
Look for the <code>Import from file</code> option. Select the corresponding JSON file from your <code>foxglove_layouts</code> folder to instantly load the configured panels for your current task.
</p>

### puzzlebot_hardware

<ul>
  <li><p align="justify"><strong>camera_calibration.py</strong> </p></li>
</ul>

### puzzlebot_perception

<ul>
  <li><p align="justify"><strong>object_detection_yolo.py:</strong> Utilizes the Ultralytics YOLO framework to identify objects in the robot's environment, processing incoming camera frames to publish bounding box coordinates and inference metadata.</p></li>
</ul>

```bash
# sim:=true: Use this parameter when working on your host PC to simulate the camera feed using your integrated webcam.
ros2 launch puzzlebot_bringup object_detection_yolo.launch.py 
```

<ul>
  <li><p align="justify"><strong>aruco_detection.py</strong> </p></li>
</ul>

<ul>
  <li><p align="justify"><strong>slam.py</strong> </p></li>
</ul>

<ul>
  <li><p align="justify"><strong>voice_recognition.py</strong> </p></li>
</ul>

### puzzlebot_navigation

<ul>
  <li><p align="justify"><strong>path_planner.py</strong> </p></li>
</ul>

<ul>
  <li><p align="justify"><strong>obstacle_avoidance.py</strong> </p></li>
</ul>

### puzzlebot_control

<ul>
  <li><p align="justify"><strong>pid_controller.py</strong> </p></li>
</ul>

<ul>
  <li><p align="justify"><strong>robot_alignment.py</strong> </p></li>
</ul>

<ul>
  <li><p align="justify"><strong>state_machine.py</strong> </p></li>
</ul>