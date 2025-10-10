#!/usr/bin/env python3
"""
Gripper Controller Test Client
夹爪控制器测试客户端

功能：
- 测试抓取和释放动作
- 监听夹爪状态

使用方法：
  rosrun gripper_controller test_client.py grip
  rosrun gripper_controller test_client.py release
  rosrun gripper_controller test_client.py status
"""

import rospy
import sys
import actionlib
import time
from gripper_controller.msg import GripperStatus, GripperControlAction, GripperControlGoal


class GripperTestClient:
    """夹爪测试客户端"""
    
    def __init__(self):
        rospy.init_node('gripper_test_client')
        
        # 创建Action客户端
        self.client = actionlib.SimpleActionClient('gripper_control', GripperControlAction)
        
        # 等待Action服务器
        rospy.loginfo("🔍 Waiting for gripper action server...")
        self.client.wait_for_server()
        rospy.loginfo("✅ Connected to gripper action server")
    
    def grip(self):
        """执行抓取"""
        goal = GripperControlGoal()
        goal.command = GripperControlGoal.GRIP
        
        rospy.loginfo("🤏 Sending grip command...")
        self.client.send_goal(goal)
        
        # 等待结果
        result = self.client.wait_for_result(rospy.Duration(20.0))
        
        print(result)
        if result:
            res = self.client.get_result()
            rospy.loginfo(f"✅ Grip result: {res.success}, {res.message}")
        else:
            rospy.logwarn("⚠️ Grip action timeout")
    
    def release(self):
        """执行释放"""
        goal = GripperControlGoal()
        goal.command = GripperControlGoal.RELEASE
        
        rospy.loginfo("🖐️ Sending release command...")
        self.client.send_goal(goal)
        
        # 等待结果
        result = self.client.wait_for_result(rospy.Duration(20.0))
        
        if result:
            res = self.client.get_result()
            rospy.loginfo(f"✅ Release result: {res.success}, {res.message}")
        else:
            rospy.logwarn("⚠️ Release action timeout")
    
    def monitor_status(self):
        """监听状态"""
        rospy.loginfo("📊 Monitoring gripper status (Ctrl+C to stop)...")
        
        def status_callback(msg):
            if msg.is_online:
                angle = (msg.position - 500) / 2000.0 * 180.0
                state_name = "GRIP" if msg.state == GripperStatus.GRIP_STATE else "RELEASE"
                rospy.loginfo(f"Status: Online, Position: {msg.position} ({angle:.1f}°), State: {state_name}")
            else:
                rospy.loginfo("Status: Offline")
        
        rospy.Subscriber('gripper_status', GripperStatus, status_callback)
        rospy.spin()


if __name__ == "__main__":
    try:
        client = GripperTestClient()
        # 使用 ROS 的关机标志与睡眠，确保 Ctrl+C/roslaunch 关闭时能优雅退出
        while not rospy.is_shutdown():
            client.grip()
            if rospy.is_shutdown():
                break
            rospy.sleep(1.0)

            client.release()
            if rospy.is_shutdown():
                break
            rospy.sleep(1.0)

    except rospy.ROSInterruptException:
        rospy.loginfo("🛑 Test client interrupted (ROS)")
    except KeyboardInterrupt:
        rospy.loginfo("🛑 Test client interrupted by user (Ctrl+C)")