# 服务器部署指南

## 部署步骤

### 1. 上传项目到服务器
```bash
# 使用scp或者git clone上传项目
scp -r google_ads/ user@server:/path/to/google_ads/
# 或
git clone <repository> /path/to/google_ads/
```

### 2. 安装Python依赖
```bash
cd /path/to/google_ads/
pip3 install -r requirements.txt
```

### 3. 配置cron定时任务
```bash
# 修改cron/crontab.txt中的路径
nano cron/crontab.txt

# 安装定时任务
crontab cron/crontab.txt

# 验证安装
crontab -l
```

## 定时任务说明

### 每小时监控 (`scripts/monitor_hourly.py`)
- **时间**: 每小时的0分钟
- **功能**: 抓取Google广告数据
- **日志**: `logs/hourly.log`

### 每日邮件 (`scripts/email_daily.py`) 
- **时间**: 每天下午6点
- **收件人**: 272363364@qq.com
- **功能**: 发送最近8天的广告监控报告
- **日志**: `logs/daily_email.log`

### 每周邮件 (`scripts/email_weekly.py`)
- **时间**: 每周一早上9点  
- **收件人**: wayne.chen@bingx.com, seven@bingx.com
- **功能**: 发送周度广告监控汇总
- **日志**: `logs/weekly_email.log`

## 脚本功能

### 1. 每小时监控脚本 (`scripts/monitor_hourly.py`)
```bash
# 手动运行
cd /path/to/google_ads/
python3 scripts/monitor_hourly.py
```

### 2. 每日邮件脚本 (`scripts/email_daily.py`)
```bash  
# 手动运行
cd /path/to/google_ads/
python3 scripts/email_daily.py
```

### 3. 每周邮件脚本 (`scripts/email_weekly.py`)
```bash
# 手动运行  
cd /path/to/google_ads/
python3 scripts/email_weekly.py
```

### 4. 统一调度器 (`scripts/scheduler.py`)
```bash
# 监控任务
python3 scripts/scheduler.py monitor

# 每日邮件
python3 scripts/scheduler.py daily-email

# 每周邮件  
python3 scripts/scheduler.py weekly-email

# 测试邮件
python3 scripts/scheduler.py test-email
```

## 日志管理

### 查看日志
```bash
# 查看每小时监控日志
tail -f logs/hourly.log

# 查看每日邮件日志  
tail -f logs/daily_email.log

# 查看每周邮件日志
tail -f logs/weekly_email.log

# 查看调度器日志
tail -f logs/scheduler.log
```

### 日志轮转 (可选)
```bash
# 配置logrotate
sudo nano /etc/logrotate.d/google_ads

# 内容:
/path/to/google_ads/logs/*.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    create 644 user user
}
```

## 维护任务

### 磁盘空间管理
```bash
# 手动清理30天前的HTML文件
find /path/to/google_ads/htmls -name "*.html" -mtime +30 -delete

# 查看HTML文件占用空间
du -sh /path/to/google_ads/htmls/
```

### 数据库备份
```bash  
# 手动备份数据库
cd /path/to/google_ads/
mkdir -p backups
cp google_ads.db backups/google_ads_$(date +%Y%m%d).db
```

## 故障排除

### 1. 检查cron任务状态
```bash
# 查看cron服务状态
systemctl status cron

# 查看cron日志
tail -f /var/log/cron.log
```

### 2. 测试脚本
```bash
# 测试监控脚本
cd /path/to/google_ads/ && python3 scripts/monitor_hourly.py

# 测试邮件发送
cd /path/to/google_ads/ && python3 scripts/scheduler.py test-email
```

### 3. 检查配置
```bash
# 验证配置文件
python3 -c "from config import EMAIL_CONFIG; print(EMAIL_CONFIG)"

# 检查数据库连接  
python3 -c "from database import AdDatabase; db = AdDatabase(); print('数据库连接正常')"
```

## 安全建议

1. **权限设置**
```bash
chmod 600 config.py  # 保护配置文件
chmod 755 scripts/*  # 脚本可执行权限
```

2. **防火墙配置**
```bash
# 只允许必要的端口访问
ufw allow ssh
ufw enable
```

3. **定期更新**
```bash
# 定期更新系统和Python包
sudo apt update && sudo apt upgrade
pip3 list --outdated
```