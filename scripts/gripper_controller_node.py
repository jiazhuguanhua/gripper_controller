#!/usr/bin/env python3
"""
Gripper Controller Node
夹爪控制节点

功能：
- Action Server：处理抓取和释放动作
- 串口通信：通过USB TTL模块与夹爪舵机通信
- 状态发布：1Hz发布夹爪在线状态和位置

作者：ROS Developer
日期：2025-10-02
版本：1.0.0
"""

import rospy
import serial
import threading
import time
from typing import Optional

import actionlib
from gripper_controller.msg import GripperStatus, GripperControlAction, GripperControlGoal, GripperControlResult, GripperControlFeedback


class ServoController:
    """舵机控制器类"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200):
        """
        初始化舵机控制器
        
        Args:
            port: 串口设备路径
            baudrate: 波特率
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.lock = threading.Lock()
        
        # 角度参数 (可修改)
        self.grip_angle = 0      # 抓取角度 (度)
        self.release_angle = 90  # 释放角度 (度)
        
        # 连接串口
        self.connect()
        
        # 初始化舵机
        if self.is_connected():
            self.initialize_servo()
    
    def connect(self) -> bool:
        """连接串口"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            rospy.loginfo(f"✅ Serial connection established: {self.port}@{self.baudrate}")
            return True
        except Exception as e:
            rospy.logerr(f"❌ Failed to connect to serial port {self.port}: {e}")
            self.serial_conn = None
            return False
    
    def is_connected(self) -> bool:
        """检查串口是否连接"""
        return self.serial_conn is not None and self.serial_conn.is_open
    
    def send_command(self, command: str) -> Optional[str]:
        """
        发送命令到舵机
        
        Args:
            command: 要发送的命令字符串
            
        Returns:
            舵机返回的响应，如果失败返回None
        """
        if not self.is_connected():
            rospy.logwarn("⚠️ Serial connection not available")
            return None
        
        try:
            with self.lock:
                # 清空输入缓冲区
                self.serial_conn.flushInput()
                
                # 发送命令
                self.serial_conn.write(command.encode())
                rospy.logdebug(f"📤 Sent command: {command.strip()}")
                
                # 等待响应
                response = self.serial_conn.readline().decode().strip()
                rospy.logdebug(f"📥 Received response: {response}")
                
                return response if response else None
                
        except Exception as e:
            rospy.logerr(f"❌ Serial communication error: {e}")
            return None
    
    def initialize_servo(self) -> bool:
        """初始化舵机"""
        rospy.loginfo("🔧 Initializing servo...")
        response = self.send_command("#000PMOD3!\r\n")
        
        if response:
            rospy.loginfo("✅ Servo initialized successfully")
            return True
        else:
            rospy.logwarn("⚠️ Servo initialization failed or no response")
            return False
    
    def angle_to_pulse(self, angle: float) -> int:
        """
        将角度转换为脉宽值
        
        Args:
            angle: 角度 (0-180度)
            
        Returns:
            脉宽值 (500-2500)
        """
        # 限制角度范围
        angle = max(0, min(180, angle))
        
        # 转换公式：500 + (angle / 180) * 2000
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
        # 转换公式：(pulse - 500) / 2000 * 180
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
        pulse = self.angle_to_pulse(angle)
        command = f"#000P{pulse:04d}!\r\n"
        
        rospy.loginfo(f"🎯 Moving servo to {angle}° (pulse: {pulse})")
        response = self.send_command(command)
        
        if response:
            rospy.loginfo(f"✅ Servo moved to {angle}°")
            return True
        else:
            rospy.logwarn(f"⚠️ Failed to move servo to {angle}°")
            return False
    
    def grip(self) -> bool:
        """执行抓取动作"""
        rospy.loginfo(f"🤏 Executing grip action (angle: {self.grip_angle}°)")
        return self.move_to_angle(self.grip_angle)
    
    def release(self) -> bool:
        """执行释放动作"""
        rospy.loginfo(f"🖐️ Executing release action (angle: {self.release_angle}°)")
        return self.move_to_angle(self.release_angle)
    
    def read_position(self) -> Optional[int]:
        """
        读取舵机当前位置
        
        Returns:
            当前脉宽值，如果读取失败返回None
        """
        response = self.send_command("#000PRAD!\r\n")
        
        if response and response.startswith("#000P") and response.endswith("!"):
            try:
                # 解析响应格式：#000P1500!
                pulse_str = response[5:-1]  # 提取脉宽数值部分
                pulse = int(pulse_str)
                rospy.logdebug(f"📊 Current servo position: {pulse} (angle: {self.pulse_to_angle(pulse):.1f}°)")
                return pulse
            except ValueError:
                rospy.logwarn(f"⚠️ Invalid position response format: {response}")
                return None
        else:
            rospy.logdebug("📭 No position response from servo (offline)")
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
        """检查舵机是否在线"""
        return self.read_position() is not None
    
    def disconnect(self):
        """断开串口连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            rospy.loginfo("🔌 Serial connection closed")


class GripperControllerNode:
    """夹爪控制节点"""
    
    def __init__(self):
        """初始化节点"""
        rospy.init_node('gripper_controller_node', anonymous=True)
        rospy.loginfo("🤖 Gripper Controller Node Starting...")
        
        # 获取参数
        self.port = rospy.get_param('~serial_port', '/dev/ttyUSB0')
        self.baudrate = rospy.get_param('~baudrate', 115200)
        
        # 初始化舵机控制器
        self.servo = ServoController(self.port, self.baudrate)
        
        # 初始化Action Server
        self.action_server = actionlib.SimpleActionServer(
            'gripper_control',
            GripperControlAction,
            self.execute_action,
            False
        )
        
        # 初始化状态发布器
        self.status_pub = rospy.Publisher('gripper_status', GripperStatus, queue_size=1)
        
        # 状态发布定时器 (1Hz)
        self.status_timer = rospy.Timer(rospy.Duration(1.0), self.publish_status)
        
        # 启动Action Server
        self.action_server.start()
        
        rospy.loginfo("✅ Gripper Controller Node initialized successfully")
        rospy.loginfo("🎯 Action server started: /gripper_control")
        rospy.loginfo("📡 Publishing status to: /gripper_status")
    
    def execute_action(self, goal: GripperControlGoal):
        """
        执行Action请求
        
        Args:
            goal: Action目标
        """
        rospy.loginfo(f"📨 Received gripper action: {goal.command}")
        
        # 创建反馈和结果消息
        feedback = GripperControlFeedback()
        result = GripperControlResult()
        
        try:
            # 执行对应的动作
            if goal.command == GripperControlGoal.GRIP:
                rospy.loginfo("🎯 Executing GRIP action...")
                success = self.servo.grip()
                action_name = "grip"
            elif goal.command == GripperControlGoal.RELEASE:
                rospy.loginfo("🎯 Executing RELEASE action...")
                success = self.servo.release()
                action_name = "release"
            else:
                rospy.logwarn(f"⚠️ Unknown action command: {goal.command}")
                result.success = False
                result.message = f"Unknown command: {goal.command}"
                self.action_server.set_aborted(result)
                return
            
            # 等待动作完成并发布反馈
            for i in range(10):  # 最多等待1秒
                if rospy.is_shutdown() or self.action_server.is_preempt_requested():
                    rospy.loginfo("🛑 Action preempted")
                    self.action_server.set_preempted()
                    return
                
                # 获取当前位置作为反馈
                current_pulse = self.servo.read_position()
                if current_pulse is not None:
                    feedback.current_position = current_pulse
                    self.action_server.publish_feedback(feedback)
                
                rospy.sleep(0.1)
            
            # 设置结果
            result.success = success
            if success:
                result.message = f"Successfully executed {action_name} action"
                rospy.loginfo(f"✅ {action_name.capitalize()} action completed successfully")
                self.action_server.set_succeeded(result)
            else:
                result.message = f"Failed to execute {action_name} action"
                rospy.logwarn(f"❌ {action_name.capitalize()} action failed")
                self.action_server.set_aborted(result)
                
        except Exception as e:
            rospy.logerr(f"❌ Action execution error: {e}")
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
            current_pulse = self.servo.read_position()
            status.is_online = (current_pulse is not None)
            
            if status.is_online:
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
            
            # 日志输出 (降低频率)
            if hasattr(self, '_last_log_time'):
                if time.time() - self._last_log_time > 5.0:  # 每5秒输出一次
                    if status.is_online:
                        angle = self.servo.pulse_to_angle(status.position)
                        state_name = "GRIP" if status.state == GripperStatus.GRIP_STATE else "RELEASE"
                        rospy.loginfo(f"📊 Gripper Status: Online, Position: {status.position} ({angle:.1f}°), State: {state_name}")
                    else:
                        rospy.loginfo("📊 Gripper Status: Offline")
                    self._last_log_time = time.time()
            else:
                self._last_log_time = time.time()
                
        except Exception as e:
            rospy.logerr(f"❌ Status publishing error: {e}")
    
    def shutdown(self):
        """节点关闭清理"""
        rospy.loginfo("🛑 Shutting down Gripper Controller Node...")
        
        # 停止定时器
        if hasattr(self, 'status_timer'):
            self.status_timer.shutdown()
        
        # 断开串口连接
        self.servo.disconnect()
        
        rospy.loginfo("✅ Gripper Controller Node shutdown completed")
    
    def run(self):
        """主运行循环"""
        rospy.loginfo("🚀 Gripper Controller Node running...")
        rospy.loginfo(f"🔌 Serial port: {self.port}@{self.baudrate}")
        rospy.loginfo("💡 Usage:")
        rospy.loginfo("  - Send action to /gripper_control")
        rospy.loginfo("  - Monitor status at /gripper_status")
        rospy.loginfo("  - Ctrl+C to stop")
        
        try:
            rospy.spin()
        except KeyboardInterrupt:
            rospy.loginfo("🛑 Interrupted by user")
        finally:
            self.shutdown()


if __name__ == "__main__":
    try:
        controller = GripperControllerNode()
        controller.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("🛑 Gripper controller node interrupted")
    except Exception as e:
        rospy.logerr(f"❌ Gripper controller node failed: {e}")