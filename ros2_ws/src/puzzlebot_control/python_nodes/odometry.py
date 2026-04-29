#!/usr/bin/env python3

import math
import sys

import rclpy
from rclpy.node import Node
from rclpy import qos
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult

from geometry_msgs.msg import Quaternion, TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32
from tf2_ros import TransformBroadcaster

def wrap_to_pi(angle):
    """
    Wraps an angle to the [-pi, pi] range.
    """
    return (angle + math.pi) % (2 * math.pi) - math.pi


def quaternion_from_yaw(yaw):
    """
    Converts a yaw angle (in radians) to a geometry_msgs/Quaternion.
    """
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q

class OdometryNode(Node):
    """
    Estimates the robot's pose (x, y, theta) by dead reckoning, using the angular
    velocities of the left and right wheels of a differential-drive robot.

    The robot's position and orientation are updated over time using Euler integration
    of the kinematic model.
    """

    def __init__(self):
        super().__init__('odometry')

        # Declare parameters
        self.declare_parameter('update_rate',  60.0)   # Hz
        self.declare_parameter('wheel_base',   0.196)  # Length between wheels in meters
        self.declare_parameter('wheel_radius', 0.05)   # Wheel radius in meters

        # Load parameters
        self.update_rate = self.get_parameter('update_rate').value
        self.wheel_base = self.get_parameter('wheel_base').value
        self.wheel_radius = self.get_parameter('wheel_radius').value

        # Register the on-set-parameters callback for dynamic parameter updates
        self.add_on_set_parameters_callback(self.parameter_callback)

        # Immediately validate the initial values
        init_params = [
            Parameter('update_rate', Parameter.Type.DOUBLE, float(self.update_rate)),
            Parameter('wheel_base', Parameter.Type.DOUBLE, float(self.wheel_base)),
            Parameter('wheel_radius', Parameter.Type.DOUBLE, float(self.wheel_radius)),
        ]
        result = self.parameter_callback(init_params)
        if not result.successful:
            raise RuntimeError(f"Parameter validation failed: {result.reason}")

        # Publisher
        self.odom_pub = self.create_publisher(
            Odometry,
            '/odom',
            qos.qos_profile_sensor_data
        )

        # Subscribers
        self.omega_l_sub = self.create_subscription(
            Float32,
            '/VelocityEncL',
            self.left_wheel_callback,
            qos.qos_profile_sensor_data
        )

        self.omega_r_sub = self.create_subscription(
            Float32,
            '/VelocityEncR',
            self.right_wheel_callback,
            qos.qos_profile_sensor_data
        )

        # TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)

        # Odometry state
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now()
        
        # Wheel angular velocities (rad/s)
        self.omega_l = 0.0
        self.omega_r = 0.0

        # Timer to publish odometry at a fixed rate
        self.timer = self.create_timer(1.0 / self.update_rate, self.update_odometry)

        self.get_logger().info("Odometry Start.")

    def left_wheel_callback(self, msg):
        """Callback to update the left wheel's angular velocity from encoder data."""
        self.omega_l = msg.data

    def right_wheel_callback(self, msg):
        """Callback to update the right wheel's angular velocity from encoder data."""
        self.omega_r = msg.data

    def update_odometry(self):
        """Computes and updates robot pose using Euler integration and publishes odometry & TF."""
        current_time = self.get_clock().now()
        
        # Calculate dt based on exact time elapsed
        dt = (current_time - self.last_time).nanoseconds / 1e9

        if dt > 0:
            # Convert wheel's angular velocities to linear velocities (m/s)
            vl = self.omega_l * self.wheel_radius
            vr = self.omega_r * self.wheel_radius

            # Compute robot velocities
            v = (vl + vr) / 2.0
            omega = (vr - vl) / self.wheel_base

            # Integrate pose using Euler's method and wrap theta to [-pi, pi]
            self.x += v * math.cos(self.theta) * dt
            self.y += v * math.sin(self.theta) * dt
            self.theta = wrap_to_pi(self.theta + omega * dt)

            # Publish standard nav_msgs/Odometry topic
            odom_msg = Odometry()
            odom_msg.header.stamp = current_time.to_msg()
            odom_msg.header.frame_id = 'odom'      
            odom_msg.child_frame_id = 'base_footprint'

            odom_msg.pose.pose.position.x = self.x
            odom_msg.pose.pose.position.y = self.y
            odom_msg.pose.pose.position.z = 0.0
            odom_msg.pose.pose.orientation = quaternion_from_yaw(self.theta)

            odom_msg.twist.twist.linear.x = v
            odom_msg.twist.twist.linear.y = 0.0
            odom_msg.twist.twist.linear.z = 0.0
            odom_msg.twist.twist.angular.x = 0.0
            odom_msg.twist.twist.angular.y = 0.0
            odom_msg.twist.twist.angular.z = omega
            
            self.odom_pub.publish(odom_msg)

            # Broadcast TF transform
            t = TransformStamped()
            t.header.stamp = current_time.to_msg()
            t.header.frame_id = 'odom'
            t.child_frame_id = 'base_footprint'

            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation = quaternion_from_yaw(self.theta)

            self.tf_broadcaster.sendTransform(t)

            # Update the last time
            self.last_time = current_time

            # Log the updated pose with ROS 2 throttle to prevent terminal spam
            self.get_logger().info(
                f"Pose -> x: {self.x:.3f}, y: {self.y:.3f}, theta: {self.theta:.3f} rad",
                throttle_duration_sec=1.0
            )

    def parameter_callback(self, params):
        """Validates and applies updated node parameters."""
        for param in params:
            if param.name == 'update_rate':
                if not isinstance(param.value, (int, float)) or param.value <= 0.0:
                    return SetParametersResult(
                        successful=False,
                        reason="update_rate must be > 0."
                    )
                self.update_rate = float(param.value)

                if hasattr(self, 'timer'):
                    self.timer.cancel()
                    self.timer = self.create_timer(1.0 / self.update_rate, self.update_odometry)

                self.get_logger().info(f"Dynamically updated update_rate to: {self.update_rate} Hz.")

            elif param.name == 'wheel_base':
                if not isinstance(param.value, (int, float)) or param.value <= 0.0:
                    return SetParametersResult(
                        successful=False,
                        reason="wheel_base must be > 0."
                    )
                self.wheel_base = float(param.value)
                self.get_logger().info(f"Dynamically updated wheel_base to: {self.wheel_base} m.")

            elif param.name == 'wheel_radius':
                if not isinstance(param.value, (int, float)) or param.value <= 0.0:
                    return SetParametersResult(
                        successful=False,
                        reason="wheel_radius must be > 0."
                    )
                self.wheel_radius = float(param.value)
                self.get_logger().info(f"Dynamically updated wheel_radius to: {self.wheel_radius} m.")

        return SetParametersResult(successful=True)

def main(args=None):
    rclpy.init(args=args)

    try:
        node = OdometryNode()
    except Exception as e:
        print(f"[FATAL] Odometry failed to initialize: {e}", file=sys.stderr)
        rclpy.shutdown()
        return

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down Odometry...")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()