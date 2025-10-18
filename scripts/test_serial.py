#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串口舵机测试脚本
用于诊断和测试舵机通信
"""

import serial
import time
import sys

def test_serial_communication(port="/dev/ttyUSB0", baudrate=115200):
    """测试串口通信"""
    
    print("=" * 60)
    print("🔧 舵机串口通信测试工具")
    print("=" * 60)
    print(f"串口: {port}")
    print(f"波特率: {baudrate}")
    print("=" * 60)
    
    try:
        # 打开串口
        print("\n📡 正在打开串口...")
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=1.0,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        
        # 清空缓冲区
        ser.flushInput()
        ser.flushOutput()
        time.sleep(0.2)
        
        print("✅ 串口已打开")
        print("=" * 60)
        
        # 测试命令列表
        test_commands = [
            ("#000PRAD!\r\n", "读取位置"),
            ("#000PMOD?\r\n", "读取工作模式"),
            ("#000P1500!\r\n", "移动到中间位置(90度)"),
        ]
        
        for command, description in test_commands:
            print(f"\n📤 测试: {description}")
            print(f"   命令: {command.strip()}")
            
            # 清空输入缓冲区
            ser.flushInput()
            
            # 发送命令
            ser.write(command.encode())
            time.sleep(0.1)
            
            # 读取响应
            response = ""
            start_time = time.time()
            while time.time() - start_time < 1.0:  # 1秒超时
                if ser.in_waiting > 0:
                    response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    time.sleep(0.01)
                else:
                    if response:
                        break
                    time.sleep(0.01)
            
            response = response.strip()
            
            if response:
                print(f"   ✅ 响应: {response}")
            else:
                print(f"   ❌ 无响应")
            
            time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("✅ 测试完成")
        print("=" * 60)
        
        # 关闭串口
        ser.close()
        
    except serial.SerialException as e:
        print(f"\n❌ 串口错误: {e}")
        print("\n💡 请检查:")
        print("   1. 串口设备是否存在")
        print("   2. 是否有权限访问串口")
        print("   3. 串口是否被其他程序占用")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False
    
    return True


if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
    baudrate = int(sys.argv[2]) if len(sys.argv) > 2 else 115200
    
    test_serial_communication(port, baudrate)
