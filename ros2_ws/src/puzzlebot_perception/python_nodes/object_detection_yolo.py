#!/usr/bin/env python3

import os
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
from ament_index_python.packages import get_package_share_directory

from puzzlebot_msgs.msg import ObjectDetectionYoloInference, ObjectDetectionYoloInferenceResult

class ObjectDetectionYolo(Node):
    def __init__(self):
        super().__init__('object_detection_yolo')
        
        self.declare_parameter('model_name', 'yolo26n.pt')
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('conf_thresh', 0.5)
        
        model_name = self.get_parameter('model_name').value
        image_topic = self.get_parameter('image_topic').value
        self.conf_thresh = self.get_parameter('conf_thresh').value
        
        try:
            pkg_share_dir = get_package_share_directory('puzzlebot_perception')
            model_path = os.path.join(pkg_share_dir, 'yolo_models', model_name)
        except Exception as e:
            self.get_logger().error(f"Could not find package share directory: {e}")
            return

        self.bridge = CvBridge()
        self.get_logger().info(f"Loading YOLO model from: {model_path}")
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            self.get_logger().error(f"Failed to load YOLO model: {e}")
            return
            
        self.img_pub = self.create_publisher(Image, 'perception/detected_objects', 10)
        self.inf_pub = self.create_publisher(ObjectDetectionYoloInference, 'perception/yolo_inference', 10)
        
        self.sub = self.create_subscription(Image, image_topic, self.image_callback, 10)

    def image_callback(self, msg):
        try:
            # Convert ROS Image to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # Run inference
            results = self.model(cv_image, verbose=False)
            
            # Prepare the custom Inference message
            inf_msg = ObjectDetectionYoloInference()
            inf_msg.header = msg.header 
            
            # Extract bounding boxes for the custom message
            for box in results[0].boxes:
                conf = float(box.conf[0])
                
                if conf >= self.conf_thresh:
                    # Ultralytics xyxy format is exactly: [xmin, ymin, xmax, ymax]
                    xyxy = box.xyxy[0].cpu().numpy()
                    cls_id = int(box.cls[0])
                    class_name = results[0].names[cls_id]
                    
                    # Populate the individual result
                    det = ObjectDetectionYoloInferenceResult()
                    det.class_name = class_name
                    det.left = int(xyxy[0])
                    det.top = int(xyxy[1])
                    det.right = int(xyxy[2])
                    det.bottom = int(xyxy[3])
                    
                    # Append it to the array
                    inf_msg.inference_results.append(det)
            
            # Publish the coordinates
            self.inf_pub.publish(inf_msg)
            
            # Plot bounding boxes on the image automatically and publish it
            annotated_frame = results[0].plot()
            out_img_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
            out_img_msg.header = msg.header
            self.img_pub.publish(out_img_msg)
            
        except Exception as e:
            self.get_logger().error(f"Error processing frame: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ObjectDetectionYolo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down generic YOLO detector...")
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()