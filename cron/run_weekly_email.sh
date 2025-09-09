#!/bin/bash

# Google Ads 每周邮件脚本
# 功能：每周一早上9点发送周报邮件

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_DIR/venv"
PYTHON_PATH="$VENV_PATH/bin/python"
LOG_FILE="$PROJECT_DIR/logs/weekly_email.log"

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

# 记录开始时间
echo "==========================================" >> "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "项目路径: $PROJECT_DIR" >> "$LOG_FILE"

# 检查虚拟环境
if [ ! -f "$PYTHON_PATH" ]; then
    echo "错误: 虚拟环境不存在: $PYTHON_PATH" >> "$LOG_FILE"
    exit 1
fi

# 检查email_weekly.py是否存在
if [ ! -f "$PROJECT_DIR/scripts/email_weekly.py" ]; then
    echo "错误: email_weekly.py文件不存在" >> "$LOG_FILE"
    exit 1
fi

# 进入项目目录并运行
cd "$PROJECT_DIR" || {
    echo "错误: 无法进入项目目录: $PROJECT_DIR" >> "$LOG_FILE"
    exit 1
}

# 激活虚拟环境并运行email_weekly.py
source "$VENV_PATH/bin/activate"
"$PYTHON_PATH" scripts/email_weekly.py >> "$LOG_FILE" 2>&1

# 记录执行结果
EXIT_CODE=$?
echo "执行结果: 退出码 $EXIT_CODE" >> "$LOG_FILE"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

exit $EXIT_CODE
