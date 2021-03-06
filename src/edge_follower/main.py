#!/usr/bin/env python
from std_msgs.msg import String
from math import pi
from sensor_msgs.msg import PointCloud2
import rospy
import pcl
import sensor_msgs.point_cloud2 as pc2
import ros_numpy
import numpy as np
import time

import follower
import ur_robot as ur
import pcl_transform as pcltf

# ROS node and topics
node_name = 'edge_follower'
target_cloud_topic = "/pcl_tf/output"
frozen_cloud_topic = '/frozen_cloud/output'

# Special signs
tick_sign = u'\u2713'.encode('utf8')
cross_sign = u'\u274c'.encode('utf8')

# Variable
store_cloud = False
frozen_cloud = None
frozen_ros_cloud = None
pcl_sub = None
frozen_pcl_publisher = None
tf_listener = None
ur_x_min,ur_x_max = -0.42,-0.05
ur_y_min,ur_y_max = 0,0.5
ur_z_min,ur_z_max = 0,0.35


# Geting PointCloud2 Data from ROS
def cloudXYZ_callback(data):
    global store_cloud,frozen_cloud

    # Pointcloud in array form
    pointcloudXYZ_np = None
    # Convert PointCloud2 to numpy array
    pointcloudXYZ = ros_numpy.numpify(data)
    global frozen_ros_cloud
    if store_cloud and frozen_ros_cloud is None:
        # Backup raw ros PointCloud2, this should only be executed once
        frozen_ros_cloud = data

    # Generate an zeros array that match the dimensions of pc
    pointcloudXYZ_np=np.zeros((pointcloudXYZ.shape[0],3))
    # Fill in the data
    pointcloudXYZ_np[:,0]=pointcloudXYZ['x']
    pointcloudXYZ_np[:,1]=pointcloudXYZ['y']
    pointcloudXYZ_np[:,2]=pointcloudXYZ['z']

    # Save the captured and transformed pointcloud
    frozen_cloud = follower.freeze_cloud(store_cloud,pointcloudXYZ_np)
    
    # Publish frozen cloud in RVIZ
    if frozen_ros_cloud is not None:
        global frozen_pcl_publisher
        frozen_pcl_publisher.publish(frozen_ros_cloud)
    
    # Start following the pointcloud
    #follower.scan_mode(frozen_cloud,ur_x_min,ur_x_max,ur_y_min,ur_y_max)
    follower.follow_mode(frozen_cloud,ur_x_min,ur_x_max,ur_y_min,ur_y_max,ur_z_min,ur_z_max)

def main():
    # ROS Node Init
    rospy.init_node(node_name)

    # PointCloud Subscriber
    pcl_sub = rospy.Subscriber(target_cloud_topic, PointCloud2, cloudXYZ_callback)

    # TF Subscriber
    global tf_listener
    tf_listener = pcltf.TransformPointCloud()

    # Frozen cloud Publisher (constant)
    global frozen_pcl_publisher
    frozen_pcl_publisher = rospy.Publisher(frozen_cloud_topic, PointCloud2, queue_size=2)

    # Init UR robot and set to ready pose
    ur.ur3_init()
    ur.ur3_set_end_effector_goal_quat(ur.init_pose[0],ur.init_pose[1],ur.init_pose[2],ur.init_pose[3],\
            ur.init_pose[4],ur.init_pose[5],ur.init_pose[6])
    print("[SYS] Robot is set to READY POSE..." + tick_sign)
    print("[SYS] Start bringing up realsense camera..."+ tick_sign)
    time.sleep(10)
    
    # Capture the pointcloud and store it
    print("[SYS] Realsense starts to capture pointcloud..." + tick_sign)
    global store_cloud
    store_cloud = True

    # Keep the node alive
    rospy.spin()

    
if __name__ == '__main__':
    main()



