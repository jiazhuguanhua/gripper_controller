# 夹爪控制器文档索引

欢迎使用夹爪控制器！这是你的文档导航中心。

## 📚 文档列表

### 1. 📖 [通信手册](COMMUNICATION_GUIDE.md) - **最详细**
完整的API文档，包含：
- 消息定义详解
- CLI命令大全
- Python示例代码（4个完整示例）
- C++示例代码（3个完整示例）
- 常见问题解答

**适合：** 需要详细了解所有功能的开发者

### 2. ⚡ [快速参考卡](QUICK_REFERENCE.md) - **最快速**
浓缩的参考手册，包含：
- 常用命令速查
- 代码片段
- 故障排查指南
- 快速开始步骤

**适合：** 需要快速查找命令或代码的用户

### 3. 📝 [README](README.md) - **入门必读**
项目概述，包含：
- 功能特性
- 安装说明
- 基本使用方法
- 硬件要求

**适合：** 第一次使用的新用户

---

## 🚀 快速开始（3步）

### 步骤1：启动节点
```bash
rosrun gripper_controller gripper_controller_node_v2.py
```

### 步骤2：测试连接
```bash
rostopic echo /gripper_status -n 1
```

### 步骤3：执行动作
```bash
python3 simple_client.py grip
```

---

## 🛠️ 工具脚本

### 测试工具
- `test_serial.py` - 串口通信测试
- `status_monitor.py` - 状态实时监听
- `simple_client.py` - 简单命令行客户端

### 使用方法
```bash
# 测试串口
python3 test_serial.py /dev/ttyUSB0 115200

# 监听状态
python3 status_monitor.py

# 执行动作
python3 simple_client.py grip
python3 simple_client.py release
```

---

## 📂 文件结构

```
gripper_controller/
├── README.md                    # 项目说明
├── COMMUNICATION_GUIDE.md       # 详细通信手册 ⭐
├── QUICK_REFERENCE.md          # 快速参考卡 ⭐
├── INDEX.md                    # 本文件
│
├── msg/
│   └── GripperStatus.msg       # 状态消息定义
│
├── action/
│   └── GripperControl.action   # Action定义
│
├── scripts/
│   ├── gripper_controller_node_v2.py  # 主节点 ⭐
│   ├── simple_client.py               # 简单客户端 ⭐
│   ├── status_monitor.py              # 状态监听器 ⭐
│   └── test_serial.py                 # 串口测试工具 ⭐
│
└── launch/
    └── gripper_controller.launch      # 启动文件
```

---

## 💡 使用场景导航

### 场景1：我是新手，第一次使用
👉 阅读顺序：
1. [README.md](README.md) - 了解基本概念
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速上手
3. 运行 `simple_client.py` - 测试功能

### 场景2：我要编写Python程序控制夹爪
👉 查看：
1. [COMMUNICATION_GUIDE.md](COMMUNICATION_GUIDE.md) - Python示例代码章节
2. `scripts/simple_client.py` - 参考实现

### 场景3：我要编写C++程序控制夹爪
👉 查看：
1. [COMMUNICATION_GUIDE.md](COMMUNICATION_GUIDE.md) - C++示例代码章节
2. CMakeLists.txt配置示例

### 场景4：夹爪无法连接/离线
👉 排查步骤：
1. 运行 `test_serial.py` - 测试串口
2. 查看 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 故障排查章节
3. 检查 [COMMUNICATION_GUIDE.md](COMMUNICATION_GUIDE.md) - 常见问题

### 场景5：需要查找特定命令或API
👉 查看：
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速查找
- [COMMUNICATION_GUIDE.md](COMMUNICATION_GUIDE.md) - 详细说明

---

## 🎓 学习路径

### 初级（Day 1）
1. ✅ 阅读 README.md
2. ✅ 启动节点并测试连接
3. ✅ 使用 simple_client.py 控制夹爪

### 中级（Day 2-3）
1. ✅ 学习消息定义和Action机制
2. ✅ 编写简单的Python客户端
3. ✅ 使用status_monitor.py监听状态

### 高级（Day 4+）
1. ✅ 编写带反馈的Action客户端
2. ✅ 集成到自己的项目中
3. ✅ 根据需求调整舵机参数

---

## 🔍 快速查找

### 我想知道...

**如何发送抓取命令？**
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 任务1

**消息格式是什么？**
→ [COMMUNICATION_GUIDE.md](COMMUNICATION_GUIDE.md) - 消息定义章节

**如何监听夹爪状态？**
→ [COMMUNICATION_GUIDE.md](COMMUNICATION_GUIDE.md) - Python示例3

**如何修改抓取角度？**
→ [COMMUNICATION_GUIDE.md](COMMUNICATION_GUIDE.md) - 常见问题Q4

**夹爪离线怎么办？**
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 故障排查

---

## 📞 支持

如果遇到问题：
1. 查看对应章节的文档
2. 运行测试工具诊断问题
3. 查看节点日志获取详细信息

---

## 🔄 版本信息

- **当前版本**: v2.0
- **最后更新**: 2025-10-18
- **Python版本**: 3.8+
- **ROS版本**: Noetic

---

**提示：** 建议将本文件添加到浏览器书签，方便快速访问！
