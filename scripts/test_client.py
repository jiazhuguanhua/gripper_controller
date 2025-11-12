#!/usr/bin/env python3
"""
Gripper Action Client - 测试客户端

演示如何使用新的 GripperControl Action 接口
"""

import rospy
import actionlib
from std_msgs.msg import Header
from gripper_controller.msg import GripperControlAction, GripperControlGoal, GripperControlResult, GripperControlFeedback


class GripperTestClient:
    def __init__(self):
        rospy.init_node('gripper_test_client')
        
        # 创建 Action 客户端
        self.client = actionlib.SimpleActionClient('gripper_control', GripperControlAction)
        
        rospy.loginfo("⏳ Waiting for action server...")
        self.client.wait_for_server()
        rospy.loginfo("✅ Connected to action server")
    
    def feedback_cb(self, feedback: GripperControlFeedback):
        """反馈回调函数"""
        rospy.loginfo(f"📊 Feedback: Position={feedback.gripper_position_deg}° at {feedback.header.stamp.secs}.{feedback.header.stamp.nsecs}")
    
    def send_grip_command(self):
        """发送抓取命令"""
        rospy.loginfo("🤏 Sending GRIP command...")
        
        # 创建 Goal
        goal = GripperControlGoal()
        goal.header = Header()
        goal.header.stamp = rospy.Time.now()
        goal.header.frame_id = "gripper_base"
        goal.command = GripperControlGoal.GRIP
        
        # 发送 Goal
        self.client.send_goal(goal, feedback_cb=self.feedback_cb)
        
        # 等待结果
        self.client.wait_for_result()
        
        # 获取结果
        result = self.client.get_result()
        state = self.client.get_state()
        
        if state == actionlib.GoalStatus.SUCCEEDED:
            if result.cmd_success:
                rospy.loginfo("✅ GRIP action SUCCEEDED: Ball gripped successfully!")
            else:
                rospy.logwarn("⚠️ GRIP action COMPLETED but FAILED to grip ball")
        else:
            rospy.logerr(f"❌ GRIP action FAILED with state: {state}")
        
        return result.cmd_success
    
    def send_release_command(self):
        """发送释放命令"""
        rospy.loginfo("🖐️ Sending RELEASE command...")
        
        # 创建 Goal
        goal = GripperControlGoal()
        goal.header = Header()
        goal.header.stamp = rospy.Time.now()
        goal.header.frame_id = "gripper_base"
        goal.command = GripperControlGoal.RELEASE
        
        # 发送 Goal
        self.client.send_goal(goal, feedback_cb=self.feedback_cb)
        
        # 等待结果
        self.client.wait_for_result()
        
        # 获取结果
        result = self.client.get_result()
        state = self.client.get_state()
        
        if state == actionlib.GoalStatus.SUCCEEDED:
            rospy.loginfo("✅ RELEASE action SUCCEEDED")
        else:
            rospy.logerr(f"❌ RELEASE action FAILED with state: {state}")
        
        return result.cmd_success


def main():
    try:
        client = GripperTestClient()
        
        rospy.loginfo("=" * 60)
        rospy.loginfo("Gripper Action Client Test")
        rospy.loginfo("=" * 60)
        
        while not rospy.is_shutdown():
            rospy.loginfo("\n📋 Menu:")
            rospy.loginfo("  1 - GRIP (抓取)")
            rospy.loginfo("  2 - RELEASE (释放)")
            rospy.loginfo("  3 - Test sequence (抓取->等待->释放)")
            rospy.loginfo("  q - Quit")
            
            choice = input("\nEnter your choice: ").strip()
            
            if choice == '1':
                client.send_grip_command()
            elif choice == '2':
                client.send_release_command()
            elif choice == '3':
                rospy.loginfo("\n🔄 Running test sequence...")
                rospy.loginfo("Step 1: GRIP")
                success = client.send_grip_command()
                if success:
                    rospy.loginfo("✅ Ball gripped! Waiting 3 seconds...")
                    rospy.sleep(3.0)
                    rospy.loginfo("Step 2: RELEASE")
                    client.send_release_command()
                    rospy.loginfo("✅ Test sequence completed!")
                else:
                    rospy.logwarn("⚠️ Grip failed, skipping release")
            elif choice.lower() == 'q':
                rospy.loginfo("👋 Bye!")
                break
            else:
                rospy.logwarn("⚠️ Invalid choice")
                
    except KeyboardInterrupt:
        rospy.loginfo("\n🛑 Interrupted by user")
    except Exception as e:
        rospy.logerr(f"❌ Error: {e}")


if __name__ == '__main__':
    main()
