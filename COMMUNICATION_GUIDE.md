# 夹爪控制器通信手册

## 📚 目录
1. [消息定义](#消息定义)
2. [CLI命令行使用](#cli命令行使用)
3. [Python示例代码](#python示例代码)
4. [C++示例代码](#c示例代码)
5. [常见问题](#常见问题)

---

## 📋 消息定义

### 1. GripperStatus (状态消息)

发布到话题：`/gripper_status`  
频率：1Hz

```
# GripperStatus.msg
bool is_online          # 夹爪是否在线
int16 position          # 舵机位置 (脉宽值: 500-2500)
uint8 GRIP_STATE = 0    # 抓取状态常量
uint8 RELEASE_STATE = 1 # 释放状态常量
uint8 state             # 当前状态 (0=抓取, 1=释放)
```

**字段说明：**
- `is_online`: `true` 表示夹爪在线，`false` 表示离线
- `position`: 舵机当前脉宽值（500对应0°，2500对应180°）
- `state`: 当前夹爪状态（`0`=抓取状态，`1`=释放状态）

### 2. GripperControlAction (Action定义)

Action服务：`/gripper_control`

#### Goal（目标）
```
# GripperControlGoal
uint8 GRIP = 0     # 抓取命令常量
uint8 RELEASE = 1  # 释放命令常量
uint8 command      # 要执行的命令 (0=抓取, 1=释放)
```

#### Result（结果）
```
# GripperControlResult
bool success       # 是否成功完成
string message     # 执行结果消息
```

#### Feedback（反馈）
```
# GripperControlFeedback
int16 current_position  # 当前位置反馈（脉宽值）
```

---

## 💻 CLI命令行使用

### 1. 查看话题列表
```bash
# 查看所有话题
rostopic list | grep gripper

# 输出：
# /gripper_control/cancel
# /gripper_control/feedback
# /gripper_control/goal
# /gripper_control/result
# /gripper_control/status
# /gripper_status
```

### 2. 监听夹爪状态
```bash
# 实时查看夹爪状态
rostopic echo /gripper_status

# 输出示例：
# is_online: True
# position: 1500
# state: 0
```

### 3. 查看消息定义
```bash
# 查看状态消息定义
rosmsg show gripper_controller/GripperStatus

# 查看Action定义
rosmsg show gripper_controller/GripperControlAction
```

### 4. 使用rostopic发送简单命令

**注意：** Action通常不通过rostopic发送，建议使用专用的客户端（见下方示例代码）。

但如果想测试，可以：
```bash
# 发布Goal（不推荐，仅用于调试）
rostopic pub /gripper_control/goal gripper_controller/GripperControlActionGoal "header:
  seq: 0
  stamp:
    secs: 0
    nsecs: 0
  frame_id: ''
goal_id:
  stamp:
    secs: 0
    nsecs: 0
  id: ''
goal:
  command: 0"  # 0=抓取, 1=释放
```

### 5. 查看Action服务器状态
```bash
# 查看当前活动的Action服务器
rostopic list | grep gripper_control

# 查看Action状态
rostopic echo /gripper_control/status
```

---

## 🐍 Python示例代码

### 示例1：简单的Action客户端

```python
#!/usr/bin/env python3
"""
简单的夹爪控制客户端
用法：python3 simple_gripper_client.py grip
     python3 simple_gripper_client.py release
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
    print("等待夹爪服务器...")
    client.wait_for_server()
    
    # 创建目标
    goal = GripperControlGoal()
    goal.command = GripperControlGoal.GRIP  # 0 = 抓取
    
    # 发送目标
    print("发送抓取命令...")
    client.send_goal(goal)
    
    # 等待结果
    client.wait_for_result(rospy.Duration(5.0))
    
    # 获取结果
    result = client.get_result()
    if result.success:
        print(f"✅ 抓取成功: {result.message}")
    else:
        print(f"❌ 抓取失败: {result.message}")

def release():
    """执行释放"""
    client = actionlib.SimpleActionClient('gripper_control', GripperControlAction)
    
    print("等待夹爪服务器...")
    client.wait_for_server()
    
    goal = GripperControlGoal()
    goal.command = GripperControlGoal.RELEASE  # 1 = 释放
    
    print("发送释放命令...")
    client.send_goal(goal)
    
    client.wait_for_result(rospy.Duration(5.0))
    
    result = client.get_result()
    if result.success:
        print(f"✅ 释放成功: {result.message}")
    else:
        print(f"❌ 释放失败: {result.message}")

if __name__ == "__main__":
    rospy.init_node('simple_gripper_client')
    
    if len(sys.argv) != 2:
        print("用法: python3 simple_gripper_client.py [grip|release]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "grip":
        grip()
    elif command == "release":
        release()
    else:
        print("未知命令。使用 'grip' 或 'release'")
```

### 示例2：带反馈的Action客户端

```python
#!/usr/bin/env python3
"""
带反馈监听的夹爪控制客户端
"""

import rospy
import actionlib
from gripper_controller.msg import (
    GripperControlAction, 
    GripperControlGoal,
    GripperControlFeedback
)

class GripperClient:
    def __init__(self):
        # 创建Action客户端
        self.client = actionlib.SimpleActionClient(
            'gripper_control', 
            GripperControlAction
        )
        
        print("等待夹爪服务器...")
        self.client.wait_for_server()
        print("✅ 已连接到夹爪服务器")
    
    def feedback_callback(self, feedback):
        """反馈回调函数"""
        # 将脉宽转换为角度
        angle = (feedback.current_position - 500) / 2000.0 * 180.0
        print(f"📊 当前位置: {feedback.current_position} ({angle:.1f}°)")
    
    def done_callback(self, state, result):
        """完成回调函数"""
        if result.success:
            print(f"✅ 动作完成: {result.message}")
        else:
            print(f"❌ 动作失败: {result.message}")
    
    def grip(self):
        """执行抓取"""
        goal = GripperControlGoal()
        goal.command = GripperControlGoal.GRIP
        
        print("🤏 发送抓取命令...")
        self.client.send_goal(
            goal,
            done_cb=self.done_callback,
            feedback_cb=self.feedback_callback
        )
        
        # 等待结果
        self.client.wait_for_result()
    
    def release(self):
        """执行释放"""
        goal = GripperControlGoal()
        goal.command = GripperControlGoal.RELEASE
        
        print("🖐️ 发送释放命令...")
        self.client.send_goal(
            goal,
            done_cb=self.done_callback,
            feedback_cb=self.feedback_callback
        )
        
        # 等待结果
        self.client.wait_for_result()

if __name__ == "__main__":
    rospy.init_node('gripper_client_with_feedback')
    
    client = GripperClient()
    
    # 执行一系列动作
    client.grip()
    rospy.sleep(2.0)
    client.release()
```

### 示例3：状态监听器

```python
#!/usr/bin/env python3
"""
夹爪状态监听器
实时显示夹爪状态
"""

import rospy
from gripper_controller.msg import GripperStatus

def status_callback(msg):
    """状态回调函数"""
    # 将脉宽转换为角度
    if msg.is_online:
        angle = (msg.position - 500) / 2000.0 * 180.0
        state_name = "抓取" if msg.state == GripperStatus.GRIP_STATE else "释放"
        
        print(f"📊 夹爪状态:")
        print(f"   在线: ✅")
        print(f"   位置: {msg.position} ({angle:.1f}°)")
        print(f"   状态: {state_name}")
    else:
        print(f"📊 夹爪状态: ❌ 离线")
    print("-" * 40)

if __name__ == "__main__":
    rospy.init_node('gripper_status_monitor')
    
    print("🚀 夹爪状态监听器启动")
    print("=" * 40)
    
    # 订阅状态话题
    rospy.Subscriber('/gripper_status', GripperStatus, status_callback)
    
    # 保持运行
    rospy.spin()
```

### 示例4：完整的应用示例

```python
#!/usr/bin/env python3
"""
完整的夹爪控制应用
包含状态监听和动作控制
"""

import rospy
import actionlib
from gripper_controller.msg import (
    GripperStatus,
    GripperControlAction,
    GripperControlGoal
)

class GripperController:
    def __init__(self):
        rospy.init_node('gripper_controller_app')
        
        # 初始化状态
        self.current_status = None
        
        # 创建Action客户端
        self.action_client = actionlib.SimpleActionClient(
            'gripper_control',
            GripperControlAction
        )
        
        # 订阅状态
        self.status_sub = rospy.Subscriber(
            '/gripper_status',
            GripperStatus,
            self.status_callback
        )
        
        print("等待夹爪服务器...")
        self.action_client.wait_for_server()
        print("✅ 已连接")
    
    def status_callback(self, msg):
        """保存最新状态"""
        self.current_status = msg
    
    def get_status(self):
        """获取当前状态"""
        if self.current_status is None:
            print("⚠️ 尚未接收到状态消息")
            return None
        
        return self.current_status
    
    def is_online(self):
        """检查是否在线"""
        status = self.get_status()
        return status.is_online if status else False
    
    def get_position(self):
        """获取当前位置（角度）"""
        status = self.get_status()
        if status and status.is_online:
            angle = (status.position - 500) / 2000.0 * 180.0
            return angle
        return None
    
    def grip(self, wait=True):
        """
        执行抓取
        
        Args:
            wait: 是否等待动作完成
        
        Returns:
            是否成功
        """
        if not self.is_online():
            print("❌ 夹爪离线，无法执行动作")
            return False
        
        goal = GripperControlGoal()
        goal.command = GripperControlGoal.GRIP
        
        print("🤏 执行抓取...")
        self.action_client.send_goal(goal)
        
        if wait:
            self.action_client.wait_for_result()
            result = self.action_client.get_result()
            return result.success
        
        return True
    
    def release(self, wait=True):
        """
        执行释放
        
        Args:
            wait: 是否等待动作完成
        
        Returns:
            是否成功
        """
        if not self.is_online():
            print("❌ 夹爪离线，无法执行动作")
            return False
        
        goal = GripperControlGoal()
        goal.command = GripperControlGoal.RELEASE
        
        print("🖐️ 执行释放...")
        self.action_client.send_goal(goal)
        
        if wait:
            self.action_client.wait_for_result()
            result = self.action_client.get_result()
            return result.success
        
        return True
    
    def print_status(self):
        """打印当前状态"""
        status = self.get_status()
        if status is None:
            print("⚠️ 无状态信息")
            return
        
        if status.is_online:
            angle = self.get_position()
            state_name = "抓取" if status.state == GripperStatus.GRIP_STATE else "释放"
            print(f"📊 夹爪状态: ✅在线 | {angle:.1f}° | {state_name}")
        else:
            print(f"📊 夹爪状态: ❌离线")

# 使用示例
if __name__ == "__main__":
    try:
        # 创建控制器
        gripper = GripperController()
        
        # 等待初始状态
        rospy.sleep(1.0)
        
        # 打印状态
        gripper.print_status()
        
        # 执行抓取
        if gripper.grip():
            print("✅ 抓取完成")
        
        rospy.sleep(2.0)
        
        # 执行释放
        if gripper.release():
            print("✅ 释放完成")
        
        # 打印最终状态
        gripper.print_status()
        
    except rospy.ROSInterruptException:
        print("程序中断")
```

---

## ⚙️ C++示例代码

### 示例1：简单的Action客户端

```cpp
// simple_gripper_client.cpp
#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <gripper_controller/GripperControlAction.h>

typedef actionlib::SimpleActionClient<gripper_controller::GripperControlAction> GripperClient;

void grip() {
    // 创建Action客户端
    GripperClient client("gripper_control", true);
    
    ROS_INFO("等待夹爪服务器...");
    client.waitForServer();
    ROS_INFO("已连接到夹爪服务器");
    
    // 创建目标
    gripper_controller::GripperControlGoal goal;
    goal.command = gripper_controller::GripperControlGoal::GRIP;
    
    // 发送目标
    ROS_INFO("发送抓取命令...");
    client.sendGoal(goal);
    
    // 等待结果
    bool finished = client.waitForResult(ros::Duration(5.0));
    
    if (finished) {
        auto result = client.getResult();
        if (result->success) {
            ROS_INFO("✅ 抓取成功: %s", result->message.c_str());
        } else {
            ROS_ERROR("❌ 抓取失败: %s", result->message.c_str());
        }
    } else {
        ROS_ERROR("❌ 动作超时");
    }
}

void release() {
    GripperClient client("gripper_control", true);
    
    ROS_INFO("等待夹爪服务器...");
    client.waitForServer();
    
    gripper_controller::GripperControlGoal goal;
    goal.command = gripper_controller::GripperControlGoal::RELEASE;
    
    ROS_INFO("发送释放命令...");
    client.sendGoal(goal);
    
    bool finished = client.waitForResult(ros::Duration(5.0));
    
    if (finished) {
        auto result = client.getResult();
        if (result->success) {
            ROS_INFO("✅ 释放成功: %s", result->message.c_str());
        } else {
            ROS_ERROR("❌ 释放失败: %s", result->message.c_str());
        }
    } else {
        ROS_ERROR("❌ 动作超时");
    }
}

int main(int argc, char** argv) {
    ros::init(argc, argv, "simple_gripper_client");
    
    if (argc != 2) {
        ROS_ERROR("用法: simple_gripper_client [grip|release]");
        return 1;
    }
    
    std::string command = argv[1];
    
    if (command == "grip") {
        grip();
    } else if (command == "release") {
        release();
    } else {
        ROS_ERROR("未知命令。使用 'grip' 或 'release'");
        return 1;
    }
    
    return 0;
}
```

### 示例2：带反馈的客户端

```cpp
// gripper_client_with_feedback.cpp
#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>
#include <gripper_controller/GripperControlAction.h>

typedef actionlib::SimpleActionClient<gripper_controller::GripperControlAction> GripperClient;

class GripperController {
public:
    GripperController() : client_("gripper_control", true) {
        ROS_INFO("等待夹爪服务器...");
        client_.waitForServer();
        ROS_INFO("✅ 已连接到夹爪服务器");
    }
    
    // 反馈回调
    void feedbackCallback(const gripper_controller::GripperControlFeedbackConstPtr& feedback) {
        double angle = (feedback->current_position - 500) / 2000.0 * 180.0;
        ROS_INFO("📊 当前位置: %d (%.1f°)", feedback->current_position, angle);
    }
    
    // 完成回调
    void doneCallback(const actionlib::SimpleClientGoalState& state,
                      const gripper_controller::GripperControlResultConstPtr& result) {
        if (result->success) {
            ROS_INFO("✅ 动作完成: %s", result->message.c_str());
        } else {
            ROS_ERROR("❌ 动作失败: %s", result->message.c_str());
        }
    }
    
    void grip() {
        gripper_controller::GripperControlGoal goal;
        goal.command = gripper_controller::GripperControlGoal::GRIP;
        
        ROS_INFO("🤏 发送抓取命令...");
        
        client_.sendGoal(goal,
            boost::bind(&GripperController::doneCallback, this, _1, _2),
            GripperClient::SimpleActiveCallback(),
            boost::bind(&GripperController::feedbackCallback, this, _1)
        );
        
        client_.waitForResult();
    }
    
    void release() {
        gripper_controller::GripperControlGoal goal;
        goal.command = gripper_controller::GripperControlGoal::RELEASE;
        
        ROS_INFO("🖐️ 发送释放命令...");
        
        client_.sendGoal(goal,
            boost::bind(&GripperController::doneCallback, this, _1, _2),
            GripperClient::SimpleActiveCallback(),
            boost::bind(&GripperController::feedbackCallback, this, _1)
        );
        
        client_.waitForResult();
    }

private:
    GripperClient client_;
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "gripper_client_with_feedback");
    
    GripperController controller;
    
    // 执行动作
    controller.grip();
    ros::Duration(2.0).sleep();
    controller.release();
    
    return 0;
}
```

### 示例3：状态监听器

```cpp
// gripper_status_monitor.cpp
#include <ros/ros.h>
#include <gripper_controller/GripperStatus.h>

void statusCallback(const gripper_controller::GripperStatus::ConstPtr& msg) {
    if (msg->is_online) {
        double angle = (msg->position - 500) / 2000.0 * 180.0;
        std::string state = (msg->state == gripper_controller::GripperStatus::GRIP_STATE) 
                            ? "抓取" : "释放";
        
        ROS_INFO("📊 夹爪状态:");
        ROS_INFO("   在线: ✅");
        ROS_INFO("   位置: %d (%.1f°)", msg->position, angle);
        ROS_INFO("   状态: %s", state.c_str());
    } else {
        ROS_INFO("📊 夹爪状态: ❌ 离线");
    }
    ROS_INFO("----------------------------------------");
}

int main(int argc, char** argv) {
    ros::init(argc, argv, "gripper_status_monitor");
    ros::NodeHandle nh;
    
    ROS_INFO("🚀 夹爪状态监听器启动");
    ROS_INFO("========================================");
    
    ros::Subscriber sub = nh.subscribe("/gripper_status", 10, statusCallback);
    
    ros::spin();
    
    return 0;
}
```

### CMakeLists.txt配置

```cmake
# 添加到你的CMakeLists.txt

find_package(catkin REQUIRED COMPONENTS
  roscpp
  actionlib
  gripper_controller
)

catkin_package(
  CATKIN_DEPENDS roscpp actionlib gripper_controller
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

# 简单客户端
add_executable(simple_gripper_client src/simple_gripper_client.cpp)
target_link_libraries(simple_gripper_client ${catkin_LIBRARIES})
add_dependencies(simple_gripper_client ${catkin_EXPORTED_TARGETS})

# 带反馈的客户端
add_executable(gripper_client_with_feedback src/gripper_client_with_feedback.cpp)
target_link_libraries(gripper_client_with_feedback ${catkin_LIBRARIES})
add_dependencies(gripper_client_with_feedback ${catkin_EXPORTED_TARGETS})

# 状态监听器
add_executable(gripper_status_monitor src/gripper_status_monitor.cpp)
target_link_libraries(gripper_status_monitor ${catkin_LIBRARIES})
add_dependencies(gripper_status_monitor ${catkin_EXPORTED_TARGETS})
```

---

## ❓ 常见问题

### Q1: 如何检查夹爪是否在线？
```bash
# 方法1: 查看状态话题
rostopic echo /gripper_status -n 1

# 方法2: Python代码
from gripper_controller.msg import GripperStatus
status = rospy.wait_for_message('/gripper_status', GripperStatus, timeout=5)
print(f"在线: {status.is_online}")
```

### Q2: 如何取消正在执行的动作？
```python
# Python
client.cancel_goal()

# C++
client.cancelGoal();
```

### Q3: 如何等待夹爪到达指定位置？
```python
# 发送目标并等待
client.send_goal(goal)
client.wait_for_result(rospy.Duration(5.0))
```

### Q4: 如何修改抓取和释放的角度？
修改节点代码中的参数：
```python
# gripper_controller_node_v2.py 第71-72行
self.grip_angle = 89      # 修改抓取角度
self.release_angle = 60   # 修改释放角度
```

### Q5: 夹爪离线了怎么办？
1. 检查串口连接
2. 检查舵机供电
3. 节点会自动尝试重连
4. 查看节点日志获取详细信息

---

## 📞 获取帮助

如果遇到问题，请：
1. 查看节点日志：`rosrun gripper_controller gripper_controller_node_v2.py`
2. 检查话题：`rostopic list | grep gripper`
3. 测试串口：`python3 test_serial.py /dev/ttyUSB0 115200`

---

**文档版本**: v1.0  
**最后更新**: 2025-10-18  
**作者**: ROS Developer
