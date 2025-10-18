# 夹爪控制器快速参考卡

## 🚀 快速开始

### 启动节点
```bash
rosrun gripper_controller gripper_controller_node_v2.py
```

### 执行动作
```bash
# 抓取
python3 simple_client.py grip

# 释放
python3 simple_client.py release
```

### 查看状态
```bash
# 方法1：命令行
rostopic echo /gripper_status

# 方法2：使用监听器
python3 status_monitor.py
```

---

## 📊 消息格式速查

### GripperStatus（状态消息）
```
话题: /gripper_status
频率: 1Hz

bool is_online      # true=在线, false=离线
int16 position      # 脉宽值 (500-2500)
uint8 state         # 0=抓取, 1=释放
```

### GripperControl（Action）
```
服务: /gripper_control

Goal:
  uint8 command     # 0=GRIP(抓取), 1=RELEASE(释放)

Result:
  bool success      # true=成功, false=失败
  string message    # 结果消息

Feedback:
  int16 current_position  # 当前位置
```

---

## 💻 Python代码片段

### 1. 基础抓取
```python
import rospy
import actionlib
from gripper_controller.msg import GripperControlAction, GripperControlGoal

rospy.init_node('gripper_user')
client = actionlib.SimpleActionClient('gripper_control', GripperControlAction)
client.wait_for_server()

goal = GripperControlGoal()
goal.command = GripperControlGoal.GRIP  # 抓取
client.send_goal(goal)
client.wait_for_result()

result = client.get_result()
print(f"结果: {result.success}")
```

### 2. 基础释放
```python
goal = GripperControlGoal()
goal.command = GripperControlGoal.RELEASE  # 释放
client.send_goal(goal)
client.wait_for_result()
```

### 3. 读取状态
```python
from gripper_controller.msg import GripperStatus

def callback(msg):
    if msg.is_online:
        angle = (msg.position - 500) / 2000.0 * 180.0
        print(f"位置: {angle:.1f}°")
    else:
        print("离线")

rospy.Subscriber('/gripper_status', GripperStatus, callback)
rospy.spin()
```

### 4. 带反馈的动作
```python
def feedback_cb(feedback):
    print(f"当前位置: {feedback.current_position}")

def done_cb(state, result):
    print(f"完成: {result.success}")

client.send_goal(goal, done_cb=done_cb, feedback_cb=feedback_cb)
```

---

## 🔧 常用命令

### 查看话题
```bash
rostopic list | grep gripper
```

### 查看消息定义
```bash
rosmsg show gripper_controller/GripperStatus
rosmsg show gripper_controller/GripperControlAction
```

### 测试串口
```bash
python3 test_serial.py /dev/ttyUSB0 115200
```

### 检查串口权限
```bash
sudo chmod 666 /dev/ttyUSB0
# 或永久添加权限
sudo usermod -a -G dialout $USER
```

---

## 🎯 常见任务

### 任务1：抓取物体
```python
# Python
client.send_goal(GripperControlGoal(command=0))
client.wait_for_result()
```

### 任务2：释放物体
```python
# Python
client.send_goal(GripperControlGoal(command=1))
client.wait_for_result()
```

### 任务3：检查是否在线
```python
# Python
status = rospy.wait_for_message('/gripper_status', GripperStatus, timeout=5)
print(f"在线: {status.is_online}")
```

### 任务4：获取当前角度
```python
# Python
status = rospy.wait_for_message('/gripper_status', GripperStatus)
if status.is_online:
    angle = (status.position - 500) / 2000.0 * 180.0
    print(f"当前角度: {angle:.1f}°")
```

---

## ⚠️ 故障排查

### 问题：夹爪离线
**解决方案：**
1. 检查 `/dev/ttyUSB0` 是否存在
2. 检查舵机供电
3. 运行测试脚本：`python3 test_serial.py`
4. 查看节点日志

### 问题：权限不足
**解决方案：**
```bash
sudo chmod 666 /dev/ttyUSB0
```

### 问题：Action无响应
**解决方案：**
1. 确认节点正在运行：`rosnode list | grep gripper`
2. 检查话题：`rostopic list | grep gripper_control`
3. 检查状态：`rostopic echo /gripper_status -n 1`

---

## 📞 获取帮助

- 详细文档：`COMMUNICATION_GUIDE.md`
- 测试工具：`test_serial.py`
- 示例代码：`scripts/` 目录

---

**快速参考卡版本**: v1.0  
**打印建议**: A4纸双面打印
