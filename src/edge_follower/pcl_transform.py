#!/usr/bin/env python


import rospy
import tf2_ros
import tf2_py as tf2

from dynamic_reconfigure.server import Server
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import PointCloud2
from tf2_sensor_msgs.tf2_sensor_msgs import do_transform_cloud
from transform_point_cloud.cfg import LookupTransformConfig

# Input/Output Topics
output_topic = '/pcl_tf/output'
target_cloud_topic = "/organized_edge_detector/output_occluding_edge"

# TF Pair
source_link = 'camera_color_optical_frame'
target_link = 'world'

class TransformPointCloud:
    def __init__(self):
        self.config = None
        self.tf_buffer = tf2_ros.Buffer(cache_time=rospy.Duration(12))
        self.tl = tf2_ros.TransformListener(self.tf_buffer)
        self.pub = rospy.Publisher(output_topic, PointCloud2, queue_size=2)
        self.sub = rospy.Subscriber(target_cloud_topic, PointCloud2,
                                    self.point_cloud_callback, queue_size=2)
        self.dr_server = Server(LookupTransformConfig, self.dr_callback)

    def dr_callback(self, config, level):
        self.config = config
        return self.config

    def point_cloud_callback(self, msg):
        lookup_time = msg.header.stamp + rospy.Duration(self.config.offset_lookup_time)
        #target_frame = msg.header.frame_id if self.config.target_frame == "" else self.config.target_frame
        #source_frame = msg.header.frame_id if self.config.source_frame == "" else self.config.source_frame
        target_frame = target_link
        source_frame = source_link
        try:
            trans = self.tf_buffer.lookup_transform(target_frame, source_frame, lookup_time,
                                                    rospy.Duration(self.config.timeout))
        except tf2.LookupException as ex:
            rospy.logwarn(str(lookup_time.to_sec()))
            rospy.logwarn(ex)
            return
        except tf2.ExtrapolationException as ex:
            rospy.logwarn(str(lookup_time.to_sec()))
            rospy.logwarn(ex)
            return
        cloud_out = do_transform_cloud(msg, trans)
        self.pub.publish(cloud_out)
