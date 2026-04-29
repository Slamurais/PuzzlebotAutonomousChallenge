#!/usr/bin/env python3

import os
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
from ament_index_python.packages import get_package_share_directory

from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult

from puzzlebot_msgs.msg import ObjectDetectionYoloInference, ObjectDetectionYoloInferenceResult

class ObjectDetectionYolo(Node):
    def __init__(self):
        super().__init__('object_detection_yolo')
        
        self.declare_parameter('model_name', 'yolo26n.pt')
        self.declare_parameter('image_topic', '/image_raw')
        self.declare_parameter('conf_thresh', 0.5)
        
        self.model_name = self.get_parameter('model_name').value
        self.image_topic = self.get_parameter('image_topic').value
        self.conf_thresh = self.get_parameter('conf_thresh').value
        
        try:
            pkg_share_dir = get_package_share_directory('puzzlebot_perception')
            model_path = os.path.join(pkg_share_dir, 'yolo_models', self.model_name)
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
            
        self.add_on_set_parameters_callback(self.parameter_callback)
            
        self.img_pub = self.create_publisher(Image, 'perception/detected_objects', 10)
        self.inf_pub = self.create_publisher(ObjectDetectionYoloInference, 'perception/yolo_inference', 10)
        
        self.sub = self.create_subscription(Image, self.image_topic, self.image_callback, 10)
        
        self.get_logger().info(f"ObjectDetectionYolo Start.")

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

    def parameter_callback(self, params: list[Parameter]) -> SetParametersResult:
        for param in params:
            if param.name == 'conf_thresh':
                if not isinstance(param.value, float) or not (0.0 <= param.value <= 1.0):
                    return SetParametersResult(successful=False, reason="conf_thresh must be a float between 0.0 and 1.0.")
                self.conf_thresh = param.value
                self.get_logger().info(f"Dynamically updated conf_thresh to: {self.conf_thresh}")
                
            elif param.name == 'image_topic':
                if not isinstance(param.value, str) or not param.value.strip():
                    return SetParametersResult(successful=False, reason="image_topic must be a non-empty string.")
                self.get_logger().warn("Changing image_topic at runtime is not supported. Restart node with the new parameter.")
                
            elif param.name == 'model_name':
                if not isinstance(param.value, str) or not param.value.strip():
                    return SetParametersResult(successful=False, reason="model_name must be a non-empty string.")
                self.get_logger().warn("Changing model_name at runtime is not supported. Restart node with the new parameter.")

        return SetParametersResult(successful=True)
    
def main(args=None):
    rclpy.init(args=args)

    try:
        node = ObjectDetectionYolo()
    except Exception as e:
        print(f"[FATAL] ObjectDetectionYolo failed to initialize: {e}", file=sys.stderr)
        rclpy.shutdown()
        return

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down ObjectDetectionYolo...")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()