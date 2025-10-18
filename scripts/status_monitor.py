#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
夹爪状态监听器
实时显示夹爪状态
"""

import rospy
from gripper_controller.msg import GripperStatus

class StatusMonitor:
    def __init__(self):
        self.last_status = None
        
    def status_callback(self, msg):
        """状态回调函数"""
        self.last_status = msg
        
        print("\n" + "=" * 50)
        print("📊 夹爪状态更新")
        print("=" * 50)
        
        # 在线状态
        if msg.is_online:
            print("🟢 状态: 在线")
            
            # 位置信息
            angle = (msg.position - 500) / 2000.0 * 180.0
            print(f"📍 位置: {msg.position} (脉宽)")
            print(f"📐 角度: {angle:.1f}°")
            
            # 状态信息
            if msg.state == GripperStatus.GRIP_STATE:
                print("✋ 动作状态: 抓取")
            else:
                print("🖐️ 动作状态: 释放")
        else:
            print("🔴 状态: 离线")
            print("⚠️  请检查:")
            print("   - 串口连接")
            print("   - 舵机供电")
            print("   - 通信参数")
        
        print("=" * 50)
    
    def get_summary(self):
        """获取状态摘要"""
        if self.last_status is None:
            return "⚠️ 尚未接收到状态消息"
        
        if self.last_status.is_online:
            angle = (self.last_status.position - 500) / 2000.0 * 180.0
            state = "抓取" if self.last_status.state == GripperStatus.GRIP_STATE else "释放"
            return f"✅ 在线 | {angle:.1f}° | {state}"
        else:
            return "❌ 离线"

if __name__ == "__main__":
    rospy.init_node('gripper_status_monitor')
    
    print("=" * 50)
    print("🚀 夹爪状态监听器")
    print("=" * 50)
    print("监听话题: /gripper_status")
    print("更新频率: 1Hz")
    print("按 Ctrl+C 停止")
    print("=" * 50)
    
    monitor = StatusMonitor()
    
    # 订阅状态话题
    rospy.Subscriber('/gripper_status', GripperStatus, monitor.status_callback)
    
    # 定时打印摘要
    rate = rospy.Rate(0.2)  # 5秒一次
    try:
        while not rospy.is_shutdown():
            rate.sleep()
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("🛑 监听器已停止")
        print(f"最后状态: {monitor.get_summary()}")
        print("=" * 50)