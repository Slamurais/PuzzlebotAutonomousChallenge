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