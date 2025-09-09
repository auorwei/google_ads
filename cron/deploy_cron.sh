#!/bin/bash

# Google Ads 定时任务部署脚本

echo "🚀 开始部署Google Ads定时任务..."

# 获取脚本目录和项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 项目目录: $PROJECT_DIR"

# 1. 给所有shell脚本添加执行权限
echo "🔧 设置脚本执行权限..."
chmod +x "$SCRIPT_DIR/run_hourly.sh"
chmod +x "$SCRIPT_DIR/run_daily_email.sh" 
chmod +x "$SCRIPT_DIR/run_weekly_email.sh"
chmod +x "$SCRIPT_DIR/deploy_cron.sh"

# 2. 创建日志目录
echo "📝 创建日志目录..."
mkdir -p "$PROJECT_DIR/logs"

# 3. 检查虚拟环境
echo "🐍 检查虚拟环境..."
if [ ! -f "$PROJECT_DIR/venv/bin/python" ]; then
    echo "❌ 错误: 虚拟环境不存在，请先创建虚拟环境"
    echo "   执行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 4. 测试脚本
echo "🧪 测试脚本是否可执行..."
for script in "run_hourly.sh" "run_daily_email.sh" "run_weekly_email.sh"; do
    if [ -x "$SCRIPT_DIR/$script" ]; then
        echo "✅ $script 可执行"
    else
        echo "❌ $script 不可执行"
        exit 1
    fi
done

# 5. 更新crontab配置文件中的路径
echo "📝 更新crontab配置文件..."
sed "s|PROJECT_PATH=.*|PROJECT_PATH=$PROJECT_DIR|g" "$SCRIPT_DIR/crontab_new.txt" > "$SCRIPT_DIR/crontab_updated.txt"

echo ""
echo "✅ 部署完成！"
echo ""
echo "📋 下一步操作："
echo "1. 安装定时任务: crontab $SCRIPT_DIR/crontab_updated.txt"
echo "2. 查看定时任务: crontab -l"
echo "3. 查看日志: tail -f $PROJECT_DIR/logs/*.log"
echo ""
echo "🔍 测试单个脚本:"
echo "   $SCRIPT_DIR/run_hourly.sh"
echo "   $SCRIPT_DIR/run_daily_email.sh"
echo "   $SCRIPT_DIR/run_weekly_email.sh"
