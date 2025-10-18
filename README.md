# Gripper Controller Package

基于ROS Noetic的夹爪控制器包，使用串口通信控制舵机夹爪。

## 📚 文档导航

**新用户请从这里开始：**

1. 📖 **[INDEX.md](INDEX.md)** - 文档索引和导航中心
2. 📘 **[COMMUNICATION_GUIDE.md](COMMUNICATION_GUIDE.md)** - 完整的通信API手册
3. ⚡ **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - 快速参考卡

## 🚀 快速开始（3步）

```bash
# 1. 启动节点
rosrun gripper_controller gripper_controller_node_v2.py

# 2. 测试连接（另一个终端）
rostopic echo /gripper_status -n 1

# 3. 执行动作
python3 scripts/simple_client.py grip      # 抓取
python3 scripts/simple_client.py release   # 释放
```

## 功能特性

- ✅ Action Server：处理抓取和释放动作
- ✅ 串口通信：通过USB TTL模块与舵机通信
- ✅ 状态发布：1Hz频率发布夹爪在线状态和位置
- ✅ 自动重连：断线后自动尝试重新连接
- ✅ 参数可调：抓取和释放角度可在代码中修改

## 硬件要求

- 舵机：支持脉宽控制的数字舵机
- 通信模块：USB转TTL模块
- 串口参数：115200波特率，8位数据位，无校验，1停止位

## 舵机通信协议

基于提供的舵机指令文档：

- 初始化：`#000PMOD3!`
- 位置控制：`#000P<pulse>T<time>!` (pulse: 500-2500, time: 毫秒)
- 位置读取：`#000PRAD!`
- 响应格式：`#000P<pulse>!`

## 安装和编译

```bash
# 进入工作空间
cd ~/vision_ws

# 编译包
catkin_make

# 刷新环境
source devel/setup.bash
```

## 使用方法

### 1. 启动夹爪控制器

```bash
# 使用launch文件启动
roslaunch gripper_controller gripper_controller.launch

# 或直接运行节点
rosrun gripper_controller gripper_controller_node.py
```

### 2. 修改角度参数

在 `gripper_controller_node.py` 中修改以下参数：

```python
# 角度参数 (可修改)
self.grip_angle = 0      # 抓取角度 (度) - 可修改此值
self.release_angle = 90  # 释放角度 (度) - 可修改此值
```

### 3. 发送动作命令

```bash
# 执行抓取动作
rosrun gripper_controller test_client.py grip

# 执行释放动作  
rosrun gripper_controller test_client.py release

# 监听夹爪状态
rosrun gripper_controller test_client.py status
```

### 4. 监听话题

```bash
# 监听夹爪状态
rostopic echo /gripper_status

# 查看action server状态
rostopic list | grep gripper
```

## 话题和服务

### Action Server
- `/gripper_control` (GripperControlAction)：夹爪控制动作

### 发布话题
- `/gripper_status` (GripperStatus)：夹爪状态信息

## 消息定义

### GripperStatus.msg
```
bool is_online          # 夹爪是否在线
int16 position          # 舵机位置 (500-2500脉宽值)
uint8 GRIP_STATE = 0    # 抓取状态常量
uint8 RELEASE_STATE = 1 # 释放状态常量  
uint8 state             # 当前状态
```

### GripperControlAction
```
# Goal
uint8 GRIP = 0     # 抓取命令
uint8 RELEASE = 1  # 释放命令
uint8 command      # 要执行的命令

# Result  
bool success       # 执行结果
string message     # 结果消息

# Feedback
int16 current_position  # 当前位置反馈
```

## 参数配置

在launch文件中可配置以下参数：

```xml
<param name="serial_port" value="/dev/ttyUSB0" />  <!-- 串口设备 -->
<param name="baudrate" value="115200" />           <!-- 波特率 -->
```

## 故障排除

1. **串口权限问题**
   ```bash
   sudo chmod 666 /dev/ttyUSB0
   # 或将用户加入dialout组
   sudo usermod -a -G dialout $USER
   ```

2. **找不到串口设备**
   ```bash
   # 查看可用串口
   ls /dev/ttyUSB*
   dmesg | grep tty
   ```

3. **舵机不响应**
   - 检查串口连接和波特率
   - 确认舵机供电正常
   - 查看节点日志输出

## 开发者信息

- 作者：Joe
- 版本：1.0.0
- 许可证：MIT