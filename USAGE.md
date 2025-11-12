# Gripper Controller 使用说明

## 📋 概述

夹爪控制器已升级为 v2.0，新增了智能抓取检测功能。

## 🎯 主要功能

### 1. Action 接口更新

#### Goal（目标）
```python
std_msgs/Header header    # 时间戳信息
uint8 GRIP = 0            # 抓取动作
uint8 RELEASE = 1         # 释放动作
uint8 command             # 要执行的命令（0=抓取, 1=释放）
```

#### Result（结果）
```python
bool cmd_success          # 动作是否成功完成
                         # GRIP时：True=成功抓到球, False=未抓到
                         # RELEASE时：始终True
```

#### Feedback（反馈）
```python
std_msgs/Header header           # 时间戳信息
int16 gripper_position_deg       # 当前夹爪位置（角度，0-180度）
```

### 2. 抓取成功判定

- **判定逻辑**：当夹爪执行 GRIP 动作后，读取最终角度
  - 如果角度 >= `grip_success_threshold`（默认 75°）→ 成功抓到球
  - 如果角度 < `grip_success_threshold` → 未抓到球（夹爪闭合到底）

- **配置参数**：
  ```bash
  # 在 launch 文件中设置阈值
  <param name="grip_success_threshold" value="75.0"/>
  ```

## 🚀 使用方法

### 启动节点

```bash
# 启动夹爪控制器
roslaunch gripper_controller gripper_controller.launch

# 或者使用自定义参数
roslaunch gripper_controller gripper_controller.launch serial_port:=/dev/ttyUSB0 grip_success_threshold:=75.0
```

### 测试客户端

```bash
# 运行交互式测试客户端
rosrun gripper_controller test_client.py
```

### Python 客户端示例

```python
#!/usr/bin/env python3
import rospy
import actionlib
from std_msgs.msg import Header
from gripper_controller.msg import GripperControlAction, GripperControlGoal

# 初始化节点
rospy.init_node('my_gripper_client')

# 创建 Action 客户端
client = actionlib.SimpleActionClient('gripper_control', GripperControlAction)
client.wait_for_server()

# 发送 GRIP 命令
goal = GripperControlGoal()
goal.header = Header()
goal.header.stamp = rospy.Time.now()
goal.header.frame_id = "gripper_base"
goal.command = GripperControlGoal.GRIP

client.send_goal(goal)
client.wait_for_result()

result = client.get_result()
if result.cmd_success:
    print("✅ Successfully gripped the ball!")
else:
    print("❌ Failed to grip the ball")
```

### C++ 客户端示例

```cpp
#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <gripper_controller/GripperControlAction.h>

// Feedback callback
void feedbackCb(const gripper_controller::GripperControlFeedbackConstPtr& feedback)
{
    ROS_INFO("Current position: %d°", feedback->gripper_position_deg);
}

// Result callback
void doneCb(const actionlib::SimpleClientGoalState& state, 
            const gripper_controller::GripperControlResultConstPtr& result)
{
    if (state == actionlib::SimpleClientGoalState::SUCCEEDED)
    {
        if (result->cmd_success)
            ROS_INFO("✅ Ball gripped successfully!");
        else
            ROS_WARN("⚠️ Failed to grip ball");
    }
}

int main(int argc, char** argv)
{
    ros::init(argc, argv, "gripper_client_cpp");
    
    // Create action client
    actionlib::SimpleActionClient<gripper_controller::GripperControlAction> 
        ac("gripper_control", true);
    
    ROS_INFO("Waiting for action server...");
    ac.waitForServer();
    
    // Create goal
    gripper_controller::GripperControlGoal goal;
    goal.header.stamp = ros::Time::now();
    goal.header.frame_id = "gripper_base";
    goal.command = gripper_controller::GripperControlGoal::GRIP;
    
    // Send goal
    ROS_INFO("Sending GRIP command...");
    ac.sendGoal(goal, &doneCb, NULL, &feedbackCb);
    
    // Wait for result
    ac.waitForResult();
    
    return 0;
}
```

## ⚙️ 配置参数

### Launch 文件参数

```xml
<launch>
  <node name="gripper_controller" pkg="gripper_controller" type="gripper_controller_node.py">
    <!-- 串口配置 -->
    <param name="serial_port" value="/dev/ttyUSB0"/>
    <param name="baudrate" value="115200"/>
    
    <!-- 抓取成功阈值（角度） -->
    <param name="grip_success_threshold" value="75.0"/>
  </node>
</launch>
```

### 节点参数说明

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `serial_port` | string | `/dev/ttyUSB0` | 串口设备路径 |
| `baudrate` | int | `115200` | 串口波特率 |
| `grip_success_threshold` | float | `75.0` | 抓取成功判定角度阈值 |

## 📊 Topic 说明

### 发布的 Topics

- `/gripper_status` (`gripper_controller/GripperStatus`)
  - 频率：1 Hz
  - 内容：夹爪在线状态、位置、状态

### Action 服务

- `/gripper_control` (`gripper_controller/GripperControlAction`)
  - 接受 GRIP 和 RELEASE 命令
  - 返回执行结果（是否成功抓到球）

## 🔧 调试技巧

### 查看夹爪状态
```bash
rostopic echo /gripper_status
```

### 查看 Action 反馈
```bash
rostopic echo /gripper_control/feedback
```

### 查看 Action 结果
```bash
rostopic echo /gripper_control/result
```

### 调整成功阈值

如果发现抓取判定不准确：

1. **增大阈值**（更严格）：
   ```bash
   rosparam set /gripper_controller/grip_success_threshold 80.0
   ```

2. **减小阈值**（更宽松）：
   ```bash
   rosparam set /gripper_controller/grip_success_threshold 70.0
   ```

3. **重启节点使参数生效**

## 📝 更新日志

### v2.0.0 (2025-11-12)
- ✅ 新增智能抓取检测功能
- ✅ Goal 添加 Header 时间戳
- ✅ Result 改为 cmd_success（表示是否抓到球）
- ✅ Feedback 改为角度值（gripper_position_deg）
- ✅ 添加可配置的抓取成功阈值
- ✅ 更新测试客户端

### v1.0.0 (2025-10-02)
- 初始版本
- 基础 Action 接口
- 串口通信
- 状态发布

## 🐛 常见问题

### Q: 为什么抓取动作返回 False？
A: 可能原因：
1. 没有球在夹爪范围内
2. 球太小或太滑，夹不住
3. `grip_success_threshold` 设置过高

### Q: 如何知道合适的阈值？
A: 
1. 观察夹爪抓到球时的最终角度
2. 观察夹爪空抓时的最终角度
3. 选择一个中间值作为阈值

### Q: RELEASE 动作的 cmd_success 有什么意义？
A: RELEASE 动作始终返回 True（只要舵机命令执行成功），因为释放动作不需要判断是否成功。

## 📧 联系方式

如有问题或建议，请提交 Issue 或联系开发团队。
