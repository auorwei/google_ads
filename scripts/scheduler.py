#!/usr/bin/env python3
"""
统一任务调度器
根据参数执行不同的任务
"""

import sys
import os
import argparse
from datetime import datetime

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import GoogleSERPScraper
from email_sender import EmailSender
from config import EMAIL_CONFIG

# 导入日志系统
from logger import project_logger

class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.logger = project_logger.get_scheduler_logger()
        self.scraper = GoogleSERPScraper()
        self.email_sender = EmailSender()
    
    def run_monitoring(self):
        """运行监控任务"""
        self.logger.info("🕐 开始监控任务")
        
        try:
            self.scraper.scrape_all_combinations()
            self.logger.info("✅ 监控任务完成")
            return True
        except Exception as e:
            self.logger.error(f"❌ 监控任务失败: {str(e)}")
            return False
    
    def send_daily_email(self):
        """发送每日邮件（下午6点给272363364@qq.com）"""
        self.logger.info("📧 开始发送每日邮件")
        
        try:
            recipients = EMAIL_CONFIG['daily_recipients']
            subject = f"[每日报告] Google广告监控 - {datetime.now().strftime('%Y-%m-%d')}"
            
            success = self.email_sender.send_email(
                subject=subject,
                recipients=recipients
            )
            
            if success:
                self.logger.info(f"✅ 每日邮件发送成功: {', '.join(recipients)}")
            else:
                self.logger.error("❌ 每日邮件发送失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 每日邮件发送异常: {str(e)}")
            return False
    
    def send_weekly_email(self):
        """发送每周邮件（周一上午9点给wayne.chen@bingx.com和seven@bingx.com）"""
        self.logger.info("📧 开始发送每周邮件")
        
        try:
            recipients = EMAIL_CONFIG['weekly_recipients']
            subject = f"[周报] Google广告监控汇总 - 第{datetime.now().isocalendar()[1]}周"
            
            success = self.email_sender.send_email(
                subject=subject,
                recipients=recipients
            )
            
            if success:
                self.logger.info(f"✅ 每周邮件发送成功: {', '.join(recipients)}")
            else:
                self.logger.error("❌ 每周邮件发送失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 每周邮件发送异常: {str(e)}")
            return False
    
    def send_test_email(self):
        """发送测试邮件"""
        self.logger.info("🧪 开始发送测试邮件")
        
        try:
            success = self.email_sender.send_test_email()
            
            if success:
                self.logger.info("✅ 测试邮件发送成功")
            else:
                self.logger.error("❌ 测试邮件发送失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 测试邮件发送异常: {str(e)}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Google广告监控任务调度器')
    
    parser.add_argument(
        'task', 
        choices=['monitor', 'daily-email', 'weekly-email', 'test-email'],
        help='要执行的任务类型'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别 (统一日志系统会自动处理)
    
    # 创建调度器
    scheduler = TaskScheduler()
    
    # 执行任务
    try:
        if args.task == 'monitor':
            success = scheduler.run_monitoring()
        elif args.task == 'daily-email':
            success = scheduler.send_daily_email()
        elif args.task == 'weekly-email':
            success = scheduler.send_weekly_email()
        elif args.task == 'test-email':
            success = scheduler.send_test_email()
        else:
            print(f"未知任务: {args.task}")
            sys.exit(1)
        
        if success:
            print("✅ 任务执行成功")
            sys.exit(0)
        else:
            print("❌ 任务执行失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("⚠️ 任务被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"💥 任务执行异常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()