# Gripper status message
bool is_online          # 夹爪是否在线
int16 position          # 舵机位置 (0-1000 对应 0-180度)
uint8 GRIP_STATE = 0    # 抓取状态
uint8 RELEASE_STATE = 1 # 释放状态
uint8 state             # 当前状态 (GRIP_STATE 或 RELEASE_STATE)