#!/usr/bin/env python3

import math
import sys

import rclpy
from rclpy.node import Node
from rclpy import qos
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult

from tf_transformations import euler_from_quaternion

from std_msgs.msg import Float32
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry

def wrap_to_pi(angle: float) -> float:
    """
    Wraps an angle to the [-pi, pi] range.
    """
    return (angle + math.pi) % (2 * math.pi) - math.pi

class PIDDifferentialPoseController(Node):
    """
    Computes velocity commands (V, Omega) using PID control to drive a differential-drive 
    robot toward a desired goal pose provided by RViz (/goal_pose).
    """

    def __init__(self):
        super().__init__('pid_differential_pose_controller')
        
        # 1. Declare parameters
        self.declare_parameter('update_rate',         30.0)        # Hz

        self.declare_parameter('Kp_V',                0.15)       
        self.declare_parameter('Ki_V',                0.0)
        self.declare_parameter('Kd_V',                0.0)

        self.declare_parameter('Kp_Omega',            0.09)
        self.declare_parameter('Ki_Omega',            0.0)
        self.declare_parameter('Kd_Omega',            0.0)

        self.declare_parameter('goal_tolerance',      0.08)         # m
        self.declare_parameter('heading_tolerance',   0.09)         # rad

        self.declare_parameter('min_linear_speed',    0.1)          # m/s
        self.declare_parameter('max_linear_speed',    0.17)         # m/s

        self.declare_parameter('min_angular_speed',  -0.15)         # rad/s
        self.declare_parameter('max_angular_speed',   0.15)         # rad/s

        self.declare_parameter('velocity_scale_factor', 1.0)
    
        # 2. Retrieve parameters
        self.update_rate            = self.get_parameter('update_rate').value

        self.Kp_V                   = self.get_parameter('Kp_V').value
        self.Ki_V                   = self.get_parameter('Ki_V').value
        self.Kd_V                   = self.get_parameter('Kd_V').value

        self.Kp_Omega               = self.get_parameter('Kp_Omega').value
        self.Ki_Omega               = self.get_parameter('Ki_Omega').value
        self.Kd_Omega               = self.get_parameter('Kd_Omega').value

        self.goal_tolerance         = self.get_parameter('goal_tolerance').value
        self.heading_tolerance      = self.get_parameter('heading_tolerance').value

        self.min_linear_speed       = self.get_parameter('min_linear_speed').value
        self.max_linear_speed       = self.get_parameter('max_linear_speed').value
        
        self.min_angular_speed      = self.get_parameter('min_angular_speed').value
        self.max_angular_speed      = self.get_parameter('max_angular_speed').value

        self.velocity_scale_factor  = self.get_parameter('velocity_scale_factor').value

        # Register dynamic parameter callback
        self.add_on_set_parameters_callback(self.parameter_callback)

        # 3. Robot state & Internals
        self.current_pose = {'x': 0.0, 'y': 0.0, 'theta': 0.0}
        self.goal_pose = {'x': 0.0, 'y': 0.0, 'theta': 0.0}
        self.goal_active = False
        
        # PID internals 
        self.integral_e_d = 0.0
        self.integral_e_theta = 0.0
        self.last_signed_e_d = 0.0
        self.last_e_theta = 0.0

        # 4. Publishers
        self.cmd_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            qos.QoSProfile(depth=10, reliability=qos.ReliabilityPolicy.RELIABLE)
        )
        
        # Telemetry topics for rqt_plot debugging
        self.signed_e_d_pub = self.create_publisher(Float32, 'pid_point_controller/signed_e_d', 10)
        self.abs_e_d_pub    = self.create_publisher(Float32, 'pid_point_controller/abs_e_d', 10)
        self.e_theta_pub    = self.create_publisher(Float32, 'pid_point_controller/e_theta', 10)

        # 5. Subscribers
        self.create_subscription(
            Odometry,
            '/odom',  # Make sure this matches your robot's odom topic
            self.odom_callback,
            qos.qos_profile_sensor_data
        )
        
        self.create_subscription(
            PoseStamped,
            '/goal_pose', # Standard RViz 2D Nav Goal topic
            self.goal_pose_callback,
            10
        )

        # 6. Timer
        self.timer = self.create_timer(1.0 / self.update_rate, self.control_loop)

        self.get_logger().info("PIDDifferentialPoseController Start.")
    
    def odom_callback(self, msg: Odometry) -> None:
        """Update the current robot pose from odometry message."""
        self.current_pose['x'] = msg.pose.pose.position.x
        self.current_pose['y'] = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        _, _, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
        self.current_pose['theta'] = yaw

    def goal_pose_callback(self, msg: PoseStamped) -> None:
        """Receive a new goal from RViz and reset PID states."""
        self.goal_pose['x'] = msg.pose.position.x
        self.goal_pose['y'] = msg.pose.position.y
        q = msg.pose.orientation
        _, _, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])
        self.goal_pose['theta'] = yaw
        
        # Reset PID memory to prevent sudden jerks from past integrations
        self.integral_e_d = 0.0
        self.integral_e_theta = 0.0
        self.last_signed_e_d = 0.0
        self.last_e_theta = 0.0
        
        self.goal_active = True
        
        BLUE = "\033[1;34m"  
        RESET = "\033[0m"      
        self.get_logger().info(f"{BLUE}New Goal Received: x={self.goal_pose['x']:.2f}, y={self.goal_pose['y']:.2f}, theta={self.goal_pose['theta']:.2f}{RESET}")
    
    def control_loop(self) -> None:
        """Main control loop running at update_rate; computes and publishes velocity commands."""
        # If no goal is active, ensure robot is stopped
        if not self.goal_active:
            self.cmd_pub.publish(Twist())
            return

        dt = 1.0 / self.update_rate

        # Compute position error components
        e_x = self.goal_pose['x'] - self.current_pose['x']
        e_y = self.goal_pose['y'] - self.current_pose['y']

        # Signed distance error along the robot's heading
        signed_e_d = e_x * math.cos(self.current_pose['theta']) + e_y * math.sin(self.current_pose['theta'])
    
        # Absolute distance error
        abs_e_d = math.hypot(e_x, e_y)

        # Compute angular error (wrapped to [-pi, pi])
        e_theta = wrap_to_pi(math.atan2(e_y, e_x) - self.current_pose['theta'])

        # Publish the intermediate error signals for debugging
        self.signed_e_d_pub.publish(Float32(data=signed_e_d))
        self.abs_e_d_pub.publish(Float32(data=abs_e_d))
        self.e_theta_pub.publish(Float32(data=e_theta))

        # Auto-stop if both errors are below thresholds
        if abs_e_d < self.goal_tolerance and abs(e_theta) < self.heading_tolerance:
            self.cmd_pub.publish(Twist())
            self.goal_active = False
            
            PURPLE = "\033[1;35m"
            RESET = "\033[0m"
            self.get_logger().info(f"{PURPLE}Goal Reached! Awaiting next command.{RESET}")
            return

        # PID control for linear velocity
        self.integral_e_d += signed_e_d * dt
        derivative_e_d = (signed_e_d - self.last_signed_e_d) / dt
        V = self.Kp_V * signed_e_d + self.Ki_V * self.integral_e_d + self.Kd_V * derivative_e_d

        # PID control for angular velocity
        self.integral_e_theta += e_theta * dt
        derivative_e_theta = (e_theta - self.last_e_theta) / dt
        Omega = self.Kp_Omega * e_theta + self.Ki_Omega * self.integral_e_theta + self.Kd_Omega * derivative_e_theta

        # Save errors for the next iteration
        self.last_signed_e_d = signed_e_d
        self.last_e_theta = e_theta

        # Apply nonlinearity handling (clamps & minimum friction limits)
        V = self.apply_velocity_constraints(V, self.min_linear_speed, self.max_linear_speed)
        Omega = self.apply_velocity_constraints(Omega, self.min_angular_speed, self.max_angular_speed)

        # Scale the final velocity output
        V = V * self.velocity_scale_factor    

        # Publish the computed command
        cmd = Twist()
        cmd.linear.x = V
        cmd.angular.z = Omega
        self.cmd_pub.publish(cmd)

        # Log control info using ROS 2 throttle (prints once per second)
        self.get_logger().info(
            f"Control -> dist_err={abs_e_d:.3f}, ang_err={e_theta:.3f}, V={V:.3f}, Omega={Omega:.3f}",
            throttle_duration_sec=1.0
        )

    def apply_velocity_constraints(self, velocity: float, min_vel: float, max_vel: float) -> float:
        """Clamp the velocity to specified minimum and maximum limits."""
        if abs(velocity) < 0.01:    
            return 0.0
            
        # Apply minimum threshold (to overcome friction/inertia)
        if abs(velocity) < abs(min_vel):
            velocity = abs(min_vel) * (1 if velocity > 0 else -1)
            
        # Apply maximum limit (saturation)
        if abs(velocity) > abs(max_vel):
            velocity = abs(max_vel) * (1 if velocity > 0 else -1)
            
        return velocity

    def parameter_callback(self, params: list[Parameter]) -> SetParametersResult:
        """Validates and applies updated node parameters dynamically."""
        for param in params:
            if param.name == 'update_rate':
                self.update_rate = float(param.value)
                self.timer.cancel()
                self.timer = self.create_timer(1.0 / self.update_rate, self.control_loop)
            elif param.name in ('Kp_V', 'Ki_V', 'Kd_V', 'Kp_Omega', 'Ki_Omega', 'Kd_Omega'):
                setattr(self, param.name, float(param.value))
            elif param.name in ('goal_tolerance', 'heading_tolerance', 'min_linear_speed', 'max_linear_speed', 'min_angular_speed', 'max_angular_speed', 'velocity_scale_factor'):
                setattr(self, param.name, float(param.value))
        return SetParametersResult(successful=True)

def main(args=None):
    rclpy.init(args=args)

    try:
        node = PIDDifferentialPoseController()
    except Exception as e:
        print(f"[FATAL] Odometry failed to initialize: {e}", file=sys.stderr)
        rclpy.shutdown()
        return

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down PIDDifferentialPoseController...")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()