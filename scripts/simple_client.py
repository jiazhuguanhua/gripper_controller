#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的夹爪控制客户端
用法：python3 simple_client.py grip
     python3 simple_client.py release
"""

import rospy
import actionlib
import sys
from gripper_controller.msg import GripperControlAction, GripperControlGoal

def grip():
    """执行抓取"""
    # 创建Action客户端
    client = actionlib.SimpleActionClient('gripper_control', GripperControlAction)
    
    # 等待服务器
    print("⏳ 等待夹爪服务器...")
    client.wait_for_server()
    print("✅ 已连接到服务器")
    
    # 创建目标
    goal = GripperControlGoal()
    goal.command = GripperControlGoal.GRIP  # 0 = 抓取
    
    # 发送目标
    print("🤏 发送抓取命令...")
    client.send_goal(goal)
    
    # 等待结果
    client.wait_for_result(rospy.Duration(5.0))
    
    # 获取结果
    result = client.get_result()
    if result and result.success:
        print(f"✅ 抓取成功: {result.message}")
        return True
    else:
        print(f"❌ 抓取失败: {result.message if result else '超时'}")
        return False

def release():
    """执行释放"""
    client = actionlib.SimpleActionClient('gripper_control', GripperControlAction)
    
    print("⏳ 等待夹爪服务器...")
    client.wait_for_server()
    print("✅ 已连接到服务器")
    
    goal = GripperControlGoal()
    goal.command = GripperControlGoal.RELEASE  # 1 = 释放
    
    print("🖐️ 发送释放命令...")
    client.send_goal(goal)
    
    client.wait_for_result(rospy.Duration(5.0))
    
    result = client.get_result()
    if result and result.success:
        print(f"✅ 释放成功: {result.message}")
        return True
    else:
        print(f"❌ 释放失败: {result.message if result else '超时'}")
        return False

if __name__ == "__main__":
    rospy.init_node('simple_gripper_client')
    
    if len(sys.argv) != 2:
        print("=" * 50)
        print("简单夹爪控制客户端")
        print("=" * 50)
        print("用法:")
        print("  python3 simple_client.py grip      # 抓取")
        print("  python3 simple_client.py release   # 释放")
        print("=" * 50)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "grip":
            success = grip()
        elif command == "release":
            success = release()
        else:
            print("❌ 未知命令。使用 'grip' 或 'release'")
            sys.exit(1)
        
        sys.exit(0 if success else 1)
        
    except rospy.ROSInterruptException:
        print("\n🛑 程序被中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")