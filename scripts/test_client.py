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
        result = self.client.wait_for_result(rospy.Duration(10.0))
        
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
        result = self.client.wait_for_result(rospy.Duration(10.0))
        
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
    if len(sys.argv) != 2:
        print("Usage:")
        print("  rosrun gripper_controller test_client.py grip")
        print("  rosrun gripper_controller test_client.py release") 
        print("  rosrun gripper_controller test_client.py status")
        sys.exit(1)
    
    command = sys.argv[1].lower()

    try:
        client = GripperTestClient()
        
        while(1):
            client.grip()
            time.sleep(1)
            client.release()
            time.sleep(1)
        if command == "grip":
            client.grip()
        elif command == "release":
            client.release()
        elif command == "status":
            client.monitor_status()
        else:
            rospy.logerr(f"❌ Unknown command: {command}")
            
    except rospy.ROSInterruptException:
        rospy.loginfo("🛑 Test client interrupted")