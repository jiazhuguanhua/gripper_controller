#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gripper Controller Node (优化版本 v2.0)
夹爪控制节点 - 支持自动重连

功能：
- Action Server：处理抓取和释放动作
- 串口通信：通过USB TTL模块与夹爪舵机通信
- 状态发布：1Hz发布夹爪在线状态和位置
- 自动重连：断开连接后自动尝试重新连接

作者：ROS Developer
日期：2025-10-18
版本：2.0.0
"""

import rospy
import serial
import threading
import time
from typing import Optional
from enum import Enum

import actionlib
from gripper_controller.msg import (
    GripperStatus,
    GripperControlAction,
    GripperControlGoal,
    GripperControlResult,
    GripperControlFeedback
)


class ConnectionState(Enum):
    """连接状态枚举"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


class ServoController:
    """
    舵机控制器类
    负责串口通信和舵机控制，支持自动重连
    """
    
    # 舵机通信协议常量
    SERVO_ID = "000"  # 舵机ID
    CMD_SET_MODE = "#{}PMOD{}!\r\n"  # 设置工作模式
    CMD_READ_MODE = "#{}PMOD?!\r\n"  # 读取工作模式
    CMD_MOVE_TIME = "#{}P{:04d}T{}!\r\n"  # 移动到指定位置(带时间)
    CMD_READ_POSITION = "#{}PRAD!\r\n"  # 读取当前位置
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200):
        """
        初始化舵机控制器
        
        Args:
            port: 串口设备路径
            baudrate: 波特率 (默认115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.lock = threading.Lock()
        self.connection_state = ConnectionState.DISCONNECTED
        
        # 舵机参数配置
        self.grip_angle = 89      # 抓取角度 (度)
        self.release_angle = 60   # 释放角度 (度)
        self.move_duration = 1000 # 移动耗时 (毫秒)
        
        # 重连参数
        self.reconnect_interval = 2.0  # 重连尝试间隔 (秒)
        self.health_check_interval = 5.0  # 健康检查间隔 (秒)
        self.reconnect_thread: Optional[threading.Thread] = None
        self.health_check_thread: Optional[threading.Thread] = None
        self.shutdown_flag = threading.Event()
        
        # 连接统计
        self.connection_attempts = 0
        self.last_successful_connection = None
        
        # 初始化连接
        self.connect()
        
        # 启动健康检查线程
        self.start_health_check()
    
    def connect(self) -> bool:
        """
        连接串口
        
        Returns:
            是否连接成功
        """
        try:
            with self.lock:
                # 如果已经连接，先关闭
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                
                # 建立新连接
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=0.5,  # 减少超时时间，提高响应速度
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                # 清空缓冲区
                self.serial_conn.flushInput()
                self.serial_conn.flushOutput()
                
                time.sleep(0.1)  # 等待串口稳定
            
            # 验证连接：使用读取工作模式指令
            if self.verify_connection():
                self.connection_state = ConnectionState.CONNECTED
                self.connection_attempts = 0
                self.last_successful_connection = time.time()
                rospy.loginfo(f"✅ 串口连接成功: {self.port}@{self.baudrate}")
                
                # 初始化舵机（设置为伺服模式）
                self.initialize_servo()
                return True
            else:
                rospy.logwarn("⚠️ 串口已打开但舵机无响应")
                self.connection_state = ConnectionState.DISCONNECTED
                if self.serial_conn:
                    self.serial_conn.close()
                    self.serial_conn = None
                return False
                
        except serial.SerialException as e:
            rospy.logwarn(f"⚠️ 串口连接失败 {self.port}: {e}")
            self.serial_conn = None
            self.connection_state = ConnectionState.DISCONNECTED
            return False
        except Exception as e:
            rospy.logerr(f"❌ 连接错误: {e}")
            self.serial_conn = None
            self.connection_state = ConnectionState.DISCONNECTED
            return False
    
    def verify_connection(self) -> bool:
        """
        验证连接是否正常（使用读取工作模式指令）
        
        Returns:
            连接是否正常
        """
        try:
            # 使用读取工作模式指令验证连接
            command = self.CMD_READ_MODE.format(self.SERVO_ID)
            response = self._send_raw_command(command, retry=1)
            
            if response and "PMOD" in response:
                rospy.logdebug(f"✅ 舵机响应正常: {response}")
                return True
            else:
                rospy.logdebug(f"❌ 舵机无响应或响应异常: {response}")
                return False
                
        except Exception as e:
            rospy.logdebug(f"❌ 连接验证失败: {e}")
            return False
    
    def is_connected(self) -> bool:
        """
        检查串口是否连接
        
        Returns:
            是否连接
        """
        return (self.serial_conn is not None and 
                self.serial_conn.is_open and 
                self.connection_state == ConnectionState.CONNECTED)
    
    def _send_raw_command(self, command: str, retry: int = 2) -> Optional[str]:
        """
        发送原始命令到舵机（底层方法，不检查连接状态）
        
        Args:
            command: 要发送的命令字符串
            retry: 重试次数
            
        Returns:
            舵机返回的响应，如果失败返回None
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            return None
        
        for attempt in range(retry + 1):
            try:
                with self.lock:
                    # 清空输入缓冲区
                    self.serial_conn.flushInput()
                    
                    # 发送命令
                    self.serial_conn.write(command.encode())
                    rospy.logdebug(f"📤 发送命令 (尝试{attempt+1}): {command.strip()}")
                    
                    # 等待响应
                    time.sleep(0.05)  # 给舵机一点时间处理
                    response = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    if response:
                        rospy.logdebug(f"📥 收到响应: {response}")
                        return response
                    else:
                        rospy.logdebug(f"📭 无响应 (尝试{attempt+1}/{retry+1})")
                        
            except (serial.SerialException, OSError) as e:
                rospy.logwarn(f"⚠️ 串口通信异常 (尝试{attempt+1}): {e}")
                # 标记为断开连接
                self.connection_state = ConnectionState.DISCONNECTED
                return None
            except Exception as e:
                rospy.logerr(f"❌ 发送命令错误 (尝试{attempt+1}): {e}")
        
        return None
    
    def send_command(self, command: str) -> Optional[str]:
        """
        发送命令到舵机（高层方法，会检查连接状态）
        
        Args:
            command: 要发送的命令字符串
            
        Returns:
            舵机返回的响应，如果失败返回None
        """
        if not self.is_connected():
            rospy.logdebug("⚠️ 串口未连接，无法发送命令")
            return None
        
        response = self._send_raw_command(command, retry=2)
        
        # 如果通信失败，标记为断开连接并触发重连
        if response is None:
            rospy.logwarn("⚠️ 舵机通信失败，标记为断开连接")
            self.connection_state = ConnectionState.DISCONNECTED
            self.trigger_reconnect()
        
        return response
    
    def initialize_servo(self) -> bool:
        """
        初始化舵机（设置为伺服模式 Mode=3）
        
        Returns:
            是否成功
        """
        rospy.loginfo("🔧 初始化舵机...")
        command = self.CMD_SET_MODE.format(self.SERVO_ID, 3)
        response = self._send_raw_command(command)
        
        if response and "OK" in response:
            rospy.loginfo("✅ 舵机初始化成功（伺服模式）")
            return True
        else:
            rospy.logwarn(f"⚠️ 舵机初始化失败或无响应: {response}")
            return False
    
    def angle_to_pulse(self, angle: float) -> int:
        """
        将角度转换为脉宽值
        
        Args:
            angle: 角度 (0-180度)
            
        Returns:
            脉宽值 (500-2500)
        """
        angle = max(0, min(180, angle))
        pulse = int(500 + (angle / 180.0) * 2000)
        return pulse
    
    def pulse_to_angle(self, pulse: int) -> float:
        """
        将脉宽值转换为角度
        
        Args:
            pulse: 脉宽值
            
        Returns:
            角度 (0-180度)
        """
        angle = (pulse - 500) / 2000.0 * 180.0
        return max(0, min(180, angle))
    
    def move_to_angle(self, angle: float) -> bool:
        """
        移动舵机到指定角度
        
        Args:
            angle: 目标角度 (0-180度)
            
        Returns:
            是否成功
        """
        if not self.is_connected():
            rospy.logwarn("⚠️ 夹爪未连接，无法执行移动")
            return False
        
        pulse = self.angle_to_pulse(angle)
        command = self.CMD_MOVE_TIME.format(self.SERVO_ID, pulse, self.move_duration)
        
        rospy.loginfo(f"🎯 移动舵机到 {angle:.1f}° (脉宽: {pulse})")
        response = self.send_command(command)
        
        if response and "OK" in response:
            rospy.loginfo(f"✅ 舵机已移动到 {angle:.1f}°")
            return True
        else:
            rospy.logwarn(f"⚠️ 移动舵机失败: {response}")
            return False
    
    def grip(self) -> bool:
        """
        执行抓取动作
        
        Returns:
            是否成功
        """
        rospy.loginfo(f"🤏 执行抓取动作 (角度: {self.grip_angle}°)")
        return self.move_to_angle(self.grip_angle)
    
    def release(self) -> bool:
        """
        执行释放动作
        
        Returns:
            是否成功
        """
        rospy.loginfo(f"🖐️ 执行释放动作 (角度: {self.release_angle}°)")
        return self.move_to_angle(self.release_angle)
    
    def read_position(self) -> Optional[int]:
        """
        读取舵机当前位置
        
        Returns:
            当前脉宽值，如果读取失败返回None
        """
        if not self.is_connected():
            return None
        
        command = self.CMD_READ_POSITION.format(self.SERVO_ID)
        response = self.send_command(command)
        
        if response and response.startswith(f"#{self.SERVO_ID}P") and response.endswith("!"):
            try:
                # 解析响应格式：#000P1500!
                pulse_str = response[5:-1]
                pulse = int(pulse_str)
                angle = self.pulse_to_angle(pulse)
                rospy.logdebug(f"📊 当前位置: {pulse} (角度: {angle:.1f}°)")
                return pulse
            except (ValueError, IndexError) as e:
                rospy.logwarn(f"⚠️ 位置响应格式无效: {response}, 错误: {e}")
                return None
        else:
            rospy.logdebug(f"📭 读取位置失败: {response}")
            return None
    
    def get_current_angle(self) -> Optional[float]:
        """
        获取当前角度
        
        Returns:
            当前角度，如果读取失败返回None
        """
        pulse = self.read_position()
        if pulse is not None:
            return self.pulse_to_angle(pulse)
        return None
    
    def is_online(self) -> bool:
        """
        检查舵机是否在线（通过读取工作模式）
        
        Returns:
            是否在线
        """
        if not self.is_connected():
            return False
        
        return self.verify_connection()
    
    def trigger_reconnect(self):
        """触发重连机制"""
        if self.connection_state == ConnectionState.RECONNECTING:
            return  # 已经在重连中
        
        self.connection_state = ConnectionState.RECONNECTING
        
        # 启动重连线程
        if self.reconnect_thread is None or not self.reconnect_thread.is_alive():
            self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
            self.reconnect_thread.start()
            rospy.loginfo("🔄 启动自动重连线程")
    
    def _reconnect_loop(self):
        """重连循环（在独立线程中运行）"""
        rospy.loginfo("🔄 开始自动重连...")
        
        while not self.shutdown_flag.is_set() and not rospy.is_shutdown():
            if self.connection_state == ConnectionState.CONNECTED:
                # 已经重连成功，退出循环
                rospy.loginfo("✅ 重连成功，退出重连循环")
                break
            
            self.connection_attempts += 1
            rospy.loginfo(f"🔄 尝试重新连接... (第 {self.connection_attempts} 次)")
            
            # 尝试连接
            if self.connect():
                rospy.loginfo("✅ 重连成功！")
                break
            else:
                rospy.logdebug(f"⏳ 等待 {self.reconnect_interval} 秒后重试...")
                time.sleep(self.reconnect_interval)
        
        if self.shutdown_flag.is_set():
            rospy.loginfo("🛑 重连线程已停止（节点关闭）")
    
    def start_health_check(self):
        """启动健康检查线程"""
        if self.health_check_thread is None or not self.health_check_thread.is_alive():
            self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.health_check_thread.start()
            rospy.logdebug("❤️ 健康检查线程已启动")
    
    def _health_check_loop(self):
        """健康检查循环（在独立线程中运行）"""
        while not self.shutdown_flag.is_set() and not rospy.is_shutdown():
            time.sleep(self.health_check_interval)
            
            if self.connection_state == ConnectionState.CONNECTED:
                # 执行健康检查
                if not self.verify_connection():
                    rospy.logwarn("⚠️ 健康检查失败，连接可能已断开")
                    self.connection_state = ConnectionState.DISCONNECTED
                    self.trigger_reconnect()
                else:
                    rospy.logdebug("✅ 健康检查通过")
    
    def disconnect(self):
        """断开串口连接"""
        self.shutdown_flag.set()  # 通知所有线程停止
        
        # 等待线程结束
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            self.reconnect_thread.join(timeout=2.0)
        
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=2.0)
        
        # 关闭串口
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                    rospy.loginfo("🔌 串口连接已关闭")
                except Exception as e:
                    rospy.logwarn(f"⚠️ 关闭串口时出错: {e}")
            
            self.serial_conn = None
            self.connection_state = ConnectionState.DISCONNECTED


class GripperControllerNode:
    """
    夹爪控制节点
    提供Action Server接口和状态发布
    """
    
    def __init__(self):
        """初始化节点"""
        rospy.init_node('gripper_controller_node', anonymous=True)
        rospy.loginfo("=" * 60)
        rospy.loginfo("🤖 夹爪控制节点启动中...")
        rospy.loginfo("=" * 60)
        
        # 获取ROS参数
        self.port = rospy.get_param('~serial_port', '/dev/ttyUSB0')
        self.baudrate = rospy.get_param('~baudrate', 115200)
        self.status_log_interval = rospy.get_param('~status_log_interval', 5.0)  # 状态日志间隔
        
        # 初始化舵机控制器
        rospy.loginfo(f"🔌 串口配置: {self.port} @ {self.baudrate} bps")
        self.servo = ServoController(self.port, self.baudrate)
        
        # 初始化Action Server
        self.action_server = actionlib.SimpleActionServer(
            'gripper_control',
            GripperControlAction,
            self.execute_action,
            False
        )
        
        # 初始化状态发布器
        self.status_pub = rospy.Publisher('gripper_status', GripperStatus, queue_size=10)
        
        # 状态发布定时器 (1Hz)
        self.status_timer = rospy.Timer(rospy.Duration(1.0), self.publish_status)
        
        # 启动Action Server
        self.action_server.start()
        
        # 状态日志
        self.last_status_log_time = time.time()
        
        rospy.loginfo("=" * 60)
        rospy.loginfo("✅ 夹爪控制节点初始化完成")
        rospy.loginfo("🎯 Action Server: /gripper_control")
        rospy.loginfo("📡 状态话题: /gripper_status")
        rospy.loginfo("=" * 60)
    
    def execute_action(self, goal: GripperControlGoal):
        """
        执行Action请求
        
        Args:
            goal: Action目标
        """
        rospy.loginfo(f"📨 收到夹爪动作请求: {goal.command}")
        
        # 创建反馈和结果消息
        feedback = GripperControlFeedback()
        result = GripperControlResult()
        
        # 检查连接状态
        if not self.servo.is_connected():
            rospy.logwarn("⚠️ 夹爪未连接，无法执行动作")
            result.success = False
            result.message = "Gripper is not connected"
            self.action_server.set_aborted(result)
            return
        
        try:
            # 执行对应的动作
            if goal.command == GripperControlGoal.GRIP:
                rospy.loginfo("🎯 执行抓取动作...")
                success = self.servo.grip()
                action_name = "grip"
            elif goal.command == GripperControlGoal.RELEASE:
                rospy.loginfo("🎯 执行释放动作...")
                success = self.servo.release()
                action_name = "release"
            else:
                rospy.logwarn(f"⚠️ 未知的动作命令: {goal.command}")
                result.success = False
                result.message = f"Unknown command: {goal.command}"
                self.action_server.set_aborted(result)
                return
            
            # 等待动作完成并发布反馈
            move_time = self.servo.move_duration / 1000.0  # 转换为秒
            feedback_steps = 10
            sleep_time = move_time / feedback_steps
            
            for i in range(feedback_steps):
                # 检查是否被取消
                if rospy.is_shutdown() or self.action_server.is_preempt_requested():
                    rospy.loginfo("🛑 动作被取消")
                    self.action_server.set_preempted()
                    return
                
                # 获取当前位置作为反馈
                current_pulse = self.servo.read_position()
                if current_pulse is not None:
                    feedback.current_position = current_pulse
                    self.action_server.publish_feedback(feedback)
                
                rospy.sleep(sleep_time)
            
            # 设置结果
            result.success = success
            if success:
                result.message = f"Successfully executed {action_name} action"
                rospy.loginfo(f"✅ {action_name.capitalize()} 动作完成")
                self.action_server.set_succeeded(result)
            else:
                result.message = f"Failed to execute {action_name} action"
                rospy.logwarn(f"❌ {action_name.capitalize()} 动作失败")
                self.action_server.set_aborted(result)
                
        except Exception as e:
            rospy.logerr(f"❌ 动作执行错误: {e}")
            result.success = False
            result.message = f"Action execution error: {str(e)}"
            self.action_server.set_aborted(result)
    
    def publish_status(self, event):
        """
        发布夹爪状态 (定时器回调)
        
        Args:
            event: 定时器事件
        """
        try:
            status = GripperStatus()
            
            # 检查舵机是否在线
            if self.servo.is_connected():
                current_pulse = self.servo.read_position()
                status.is_online = (current_pulse is not None)
            else:
                status.is_online = False
                current_pulse = None
            
            if status.is_online and current_pulse is not None:
                # 舵机在线，获取位置信息
                status.position = current_pulse
                
                # 判断当前状态 (根据角度判断)
                current_angle = self.servo.pulse_to_angle(current_pulse)
                grip_diff = abs(current_angle - self.servo.grip_angle)
                release_diff = abs(current_angle - self.servo.release_angle)
                
                if grip_diff < release_diff:
                    status.state = GripperStatus.GRIP_STATE
                else:
                    status.state = GripperStatus.RELEASE_STATE
            else:
                # 舵机离线
                status.position = -1  # 无效位置
                status.state = GripperStatus.GRIP_STATE  # 默认状态
            
            # 发布状态
            self.status_pub.publish(status)
            
            # 定期输出日志
            current_time = time.time()
            if current_time - self.last_status_log_time >= self.status_log_interval:
                if status.is_online:
                    angle = self.servo.pulse_to_angle(status.position)
                    state_name = "抓取" if status.state == GripperStatus.GRIP_STATE else "释放"
                    rospy.loginfo(
                        f"📊 夹爪状态: ✅在线 | "
                        f"位置: {status.position} ({angle:.1f}°) | "
                        f"状态: {state_name}"
                    )
                else:
                    conn_state = self.servo.connection_state.value
                    rospy.loginfo(f"📊 夹爪状态: ❌离线 | 连接状态: {conn_state}")
                
                self.last_status_log_time = current_time
                
        except Exception as e:
            rospy.logerr(f"❌ 状态发布错误: {e}")
    
    def shutdown(self):
        """节点关闭清理"""
        rospy.loginfo("=" * 60)
        rospy.loginfo("🛑 夹爪控制节点关闭中...")
        rospy.loginfo("=" * 60)
        
        # 停止定时器
        if hasattr(self, 'status_timer'):
            self.status_timer.shutdown()
            rospy.loginfo("⏹️ 状态定时器已停止")
        
        # 断开串口连接
        self.servo.disconnect()
        
        rospy.loginfo("✅ 夹爪控制节点已关闭")
        rospy.loginfo("=" * 60)
    
    def run(self):
        """主运行循环"""
        rospy.loginfo("🚀 夹爪控制节点运行中...")
        rospy.loginfo("💡 使用方法:")
        rospy.loginfo("  - 发送 Action 到 /gripper_control")
        rospy.loginfo("  - 监控状态：rostopic echo /gripper_status")
        rospy.loginfo("  - 停止节点：Ctrl+C")
        rospy.loginfo("=" * 60)
        
        try:
            rospy.spin()
        except KeyboardInterrupt:
            rospy.loginfo("🛑 用户中断")
        finally:
            self.shutdown()


def main():
    """主函数"""
    try:
        controller = GripperControllerNode()
        controller.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("🛑 ROS中断")
    except Exception as e:
        rospy.logerr(f"❌ 节点启动失败: {e}")
        import traceback
        rospy.logerr(traceback.format_exc())


if __name__ == "__main__":
    main()
