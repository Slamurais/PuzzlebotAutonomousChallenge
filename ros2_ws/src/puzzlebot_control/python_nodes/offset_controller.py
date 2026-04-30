#!/usr/bin/env python3

""" Offset Controller for Puzzlebot Navigation

    Description:
        This node implements a controller that controls a point on the robot that is offset from the center of rotation.
        This allows for controlling both x and y velocities of the robot, which can be useful for certain navigation tasks
    
    Publishers:
        - cmd_vel (Twist): The velocity command to be sent to the robot
    
    Subscriptions:
        - /puzzlebot/pose (Pose): The current pose of the robot, used to calculate the offset control commands

"""
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import Float32


class OffsetControl(Node):

    def __init__(self):
        super().__init__('offset_control')

        # Publishers
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)

    def offset_callback(self, msg: Float32):
        cmd = Twist()
        # TODO: implement control logic using msg.data
        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = OffsetControl()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()