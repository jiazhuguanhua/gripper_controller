#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gripper Controller Cycle Test Client
夹爪控制器循环测试客户端

功能：
- 循环执行抓取和释放动作
- 实时显示执行状态和结果
- 支持自定义循环次数和等待时间

使用方法：
  rosrun gripper_controller test_client_cycle.py
  rosrun gripper_controller test_client_cycle.py --cycles 10 --delay 2.0
  
参数：
  --cycles: 循环次数（默认：无限循环，使用 Ctrl+C 停止）
  --delay:  每次动作后的等待时间（秒，默认：2.0）
  --timeout: Action 超时时间（秒，默认：5.0）
"""

import rospy
import sys
import actionlib
import time
import argparse
from gripper_controller.msg import GripperStatus, GripperControlAction, GripperControlGoal


class GripperCycleTestClient:
    """夹爪循环测试客户端"""
    
    def __init__(self, action_timeout=5.0):
        """
        初始化客户端
        
        Args:
            action_timeout: Action 超时时间（秒）
        """
        rospy.init_node('gripper_cycle_test_client', anonymous=True)
        
        self.action_timeout = action_timeout
        self.cycle_count = 0
        self.success_count = 0
        self.fail_count = 0
        
        # 创建Action客户端
        self.client = actionlib.SimpleActionClient('gripper_control', GripperControlAction)
        
        # 等待Action服务器
        rospy.loginfo("=" * 60)
        rospy.loginfo("🔍 等待夹爪 Action 服务器...")
        server_ready = self.client.wait_for_server(rospy.Duration(10.0))
        
        if not server_ready:
            rospy.logerr("❌ 无法连接到 Action 服务器，请确保夹爪控制节点正在运行")
            rospy.logerr("   启动命令: rosrun gripper_controller gripper_controller_node_v2.py")
            sys.exit(1)
        
        rospy.loginfo("✅ 已连接到夹爪 Action 服务器")
        rospy.loginfo("=" * 60)
    
    def grip(self):
        """
        执行抓取动作
        
        Returns:
            bool: 是否成功
        """
        goal = GripperControlGoal()
        goal.command = GripperControlGoal.GRIP
        
        rospy.loginfo("🤏 发送抓取命令...")
        self.client.send_goal(goal)
        
        # 等待结果
        finished = self.client.wait_for_result(rospy.Duration(self.action_timeout))
        
        if finished:
            res = self.client.get_result()
            if res.success:
                rospy.loginfo(f"   ✅ 抓取成功: {res.message}")
                return True
            else:
                rospy.logwarn(f"   ❌ 抓取失败: {res.message}")
                return False
        else:
            rospy.logwarn(f"   ⚠️ 抓取超时（{self.action_timeout}秒）")
            self.client.cancel_goal()
            return False
    
    def release(self):
        """
        执行释放动作
        
        Returns:
            bool: 是否成功
        """
        goal = GripperControlGoal()
        goal.command = GripperControlGoal.RELEASE
        
        rospy.loginfo("🖐️  发送释放命令...")
        self.client.send_goal(goal)
        
        # 等待结果
        finished = self.client.wait_for_result(rospy.Duration(self.action_timeout))
        
        if finished:
            res = self.client.get_result()
            if res.success:
                rospy.loginfo(f"   ✅ 释放成功: {res.message}")
                return True
            else:
                rospy.logwarn(f"   ❌ 释放失败: {res.message}")
                return False
        else:
            rospy.logwarn(f"   ⚠️ 释放超时（{self.action_timeout}秒）")
            self.client.cancel_goal()
            return False
    
    def run_cycle(self, max_cycles=None, delay=2.0):
        """
        运行循环测试
        
        Args:
            max_cycles: 最大循环次数（None 表示无限循环）
            delay: 每次动作后的等待时间（秒）
        """
        rospy.loginfo("=" * 60)
        rospy.loginfo("🚀 开始夹爪循环测试")
        if max_cycles:
            rospy.loginfo(f"📊 循环次数: {max_cycles}")
        else:
            rospy.loginfo("📊 循环次数: 无限（Ctrl+C 停止）")
        rospy.loginfo(f"⏱️  动作间隔: {delay} 秒")
        rospy.loginfo(f"⏱️  超时时间: {self.action_timeout} 秒")
        rospy.loginfo("=" * 60)
        
        start_time = time.time()
        
        try:
            while not rospy.is_shutdown():
                # 检查是否达到最大循环次数
                if max_cycles and self.cycle_count >= max_cycles:
                    rospy.loginfo("=" * 60)
                    rospy.loginfo(f"✅ 已完成 {max_cycles} 次循环测试")
                    break
                
                self.cycle_count += 1
                rospy.loginfo("")
                rospy.loginfo("─" * 60)
                rospy.loginfo(f"🔄 第 {self.cycle_count} 次循环")
                rospy.loginfo("─" * 60)
                
                # 执行抓取
                grip_success = self.grip()
                if grip_success:
                    self.success_count += 1
                else:
                    self.fail_count += 1
                
                if rospy.is_shutdown():
                    break
                
                rospy.loginfo(f"⏳ 等待 {delay} 秒...")
                rospy.sleep(delay)
                
                if rospy.is_shutdown():
                    break
                
                # 执行释放
                release_success = self.release()
                if release_success:
                    self.success_count += 1
                else:
                    self.fail_count += 1
                
                if rospy.is_shutdown():
                    break
                
                rospy.loginfo(f"⏳ 等待 {delay} 秒...")
                rospy.sleep(delay)
                
        except KeyboardInterrupt:
            rospy.loginfo("")
            rospy.loginfo("🛑 用户中断（Ctrl+C）")
        except rospy.ROSInterruptException:
            rospy.loginfo("🛑 ROS 中断")
        finally:
            self.print_summary(start_time)
    
    def print_summary(self, start_time):
        """
        打印测试摘要
        
        Args:
            start_time: 测试开始时间
        """
        elapsed_time = time.time() - start_time
        total_actions = self.success_count + self.fail_count
        success_rate = (self.success_count / total_actions * 100) if total_actions > 0 else 0
        
        rospy.loginfo("")
        rospy.loginfo("=" * 60)
        rospy.loginfo("📊 测试摘要")
        rospy.loginfo("=" * 60)
        rospy.loginfo(f"🔄 完成循环: {self.cycle_count} 次")
        rospy.loginfo(f"📈 总动作数: {total_actions} 次（{self.cycle_count * 2} 预期）")
        rospy.loginfo(f"✅ 成功次数: {self.success_count} 次")
        rospy.loginfo(f"❌ 失败次数: {self.fail_count} 次")
        rospy.loginfo(f"📊 成功率: {success_rate:.1f}%")
        rospy.loginfo(f"⏱️  总耗时: {elapsed_time:.1f} 秒")
        if self.cycle_count > 0:
            avg_time = elapsed_time / self.cycle_count
            rospy.loginfo(f"⏱️  平均每次循环: {avg_time:.1f} 秒")
        rospy.loginfo("=" * 60)


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='夹爪控制器循环测试客户端',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 无限循环（Ctrl+C 停止）
  rosrun gripper_controller test_client_cycle.py
  
  # 循环 10 次
  rosrun gripper_controller test_client_cycle.py --cycles 10
  
  # 循环 20 次，每次等待 3 秒
  rosrun gripper_controller test_client_cycle.py --cycles 20 --delay 3.0
  
  # 自定义超时时间
  rosrun gripper_controller test_client_cycle.py --timeout 10.0
        """
    )
    
    parser.add_argument(
        '--cycles', 
        type=int, 
        default=None,
        help='循环次数（默认：无限循环）'
    )
    
    parser.add_argument(
        '--delay', 
        type=float, 
        default=2.0,
        help='每次动作后的等待时间（秒，默认：2.0）'
    )
    
    parser.add_argument(
        '--timeout', 
        type=float, 
        default=5.0,
        help='Action 超时时间（秒，默认：5.0）'
    )
    
    args = parser.parse_args()
    
    # 创建客户端并运行测试
    try:
        client = GripperCycleTestClient(action_timeout=args.timeout)
        client.run_cycle(max_cycles=args.cycles, delay=args.delay)
    except Exception as e:
        rospy.logerr(f"❌ 测试客户端错误: {e}")
        import traceback
        rospy.logerr(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()