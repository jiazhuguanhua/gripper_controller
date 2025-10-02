cmake_minimum_required(VERSION 3.0.2)
project(gripper_controller)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  actionlib
  actionlib_msgs
  message_generation
)

# Generate messages in the 'msg' folder
add_message_files(
  FILES
  GripperStatus.msg
)

# Generate actions in the 'action' folder
add_action_files(
  FILES
  GripperControl.action
)

# Generate added messages and services with any dependencies listed here
generate_messages(
  DEPENDENCIES
  std_msgs
  actionlib_msgs
)

catkin_package(
  CATKIN_DEPENDS rospy std_msgs actionlib actionlib_msgs message_runtime
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

# Mark executable scripts (Python etc.) for installation
catkin_install_python(PROGRAMS
  scripts/gripper_controller_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# Mark other files for installation (e.g. launch and bag files, etc.)
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)