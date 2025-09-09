#!/bin/bash
"""
Cron任务自动设置脚本
自动配置Google广告监控系统的定时任务
"""

set -e  # 遇到错误立即退出

# 颜色输出函数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取项目路径
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
CRON_FILE="$PROJECT_DIR/cron/crontab.txt"
LOGS_DIR="$PROJECT_DIR/logs"

echo_info "🚀 开始设置Google广告监控定时任务"
echo_info "项目路径: $PROJECT_DIR"

# 检查必要文件是否存在
if [ ! -f "$CRON_FILE" ]; then
    echo_error "Cron配置文件不存在: $CRON_FILE"
    exit 1
fi

# 创建日志目录
if [ ! -d "$LOGS_DIR" ]; then
    echo_info "创建日志目录: $LOGS_DIR"
    mkdir -p "$LOGS_DIR"
fi

# 检查Python环境
PYTHON_CMD=""
if [ -f "$PROJECT_DIR/venv/bin/python3" ]; then
    PYTHON_CMD="$PROJECT_DIR/venv/bin/python3"
    echo_info "使用虚拟环境Python: $PYTHON_CMD"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=$(which python3)
    echo_info "使用系统Python: $PYTHON_CMD"
else
    echo_error "未找到Python3，请先安装Python3"
    exit 1
fi

# 检查依赖包
echo_info "检查Python依赖..."
if ! $PYTHON_CMD -c "import requests, sqlite3, smtplib" &> /dev/null; then
    echo_warning "某些Python依赖包可能未安装，请运行: pip install -r requirements.txt"
fi

# 创建临时cron文件，替换路径变量
TEMP_CRON_FILE=$(mktemp)
echo_info "生成cron配置..."

# 替换配置文件中的路径变量
sed \
    -e "s|PROJECT_PATH=.*|PROJECT_PATH=$PROJECT_DIR|g" \
    -e "s|PYTHON=.*|PYTHON=$PYTHON_CMD|g" \
    "$CRON_FILE" > "$TEMP_CRON_FILE"

echo_info "生成的cron配置:"
echo "----------------------------------------"
grep -v "^#" "$TEMP_CRON_FILE" | grep -v "^$"
echo "----------------------------------------"

# 询问用户确认
echo ""
read -p "是否要安装这些定时任务? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo_warning "用户取消安装"
    rm -f "$TEMP_CRON_FILE"
    exit 0
fi

# 备份现有的crontab
echo_info "备份现有crontab..."
if crontab -l > /dev/null 2>&1; then
    crontab -l > "$PROJECT_DIR/cron/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
    echo_success "现有crontab已备份"
fi

# 安装新的crontab
echo_info "安装新的cron任务..."
if crontab "$TEMP_CRON_FILE"; then
    echo_success "✅ Cron任务安装成功!"
else
    echo_error "❌ Cron任务安装失败"
    rm -f "$TEMP_CRON_FILE"
    exit 1
fi

# 清理临时文件
rm -f "$TEMP_CRON_FILE"

# 显示安装结果
echo_success "🎉 定时任务设置完成!"
echo ""
echo_info "📅 任务计划:"
echo "  • 每小时监控: 抓取广告数据"
echo "  • 每天18:00: 发邮件给 272363364@qq.com"
echo "  • 每周一09:00: 发邮件给 wayne.chen@bingx.com, seven@bingx.com"
echo ""
echo_info "📝 查看当前crontab:"
echo "  crontab -l"
echo ""
echo_info "📋 查看日志:"
echo "  tail -f $LOGS_DIR/cron.log"
echo "  tail -f $LOGS_DIR/scheduler.log"
echo ""
echo_info "🛠️ 管理命令:"
echo "  删除所有任务: crontab -r"
echo "  编辑任务: crontab -e"
echo "  测试监控: cd $PROJECT_DIR && python scripts/scheduler.py monitor"
echo "  测试邮件: cd $PROJECT_DIR && python scripts/scheduler.py test-email"
echo ""
echo_warning "⚠️ 注意事项:"
echo "  1. 确保系统时间正确"
echo "  2. 定期检查日志文件"
echo "  3. 监控磁盘空间 (HTML文件会积累)"
echo "  4. 如需修改邮件收件人，请编辑 config.py"