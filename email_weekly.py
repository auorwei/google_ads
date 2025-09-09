#!/usr/bin/env python3
"""
每周邮件发送脚本
每周一早上9点给wayne.chen@bingx.com和seven@bingx.com发送邮件
"""

import sys
import os
from datetime import datetime

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_sender import EmailSender
from config import EMAIL_CONFIG

# 导入日志系统
from logger import project_logger

def main():
    """主函数"""
    logger = project_logger.get_weekly_email_logger()
    
    week_number = datetime.now().isocalendar()[1]
    logger.info(f"📧 开始发送第{week_number}周邮件")
    logger.info(f"收件人: {EMAIL_CONFIG['weekly_recipients']}")
    
    try:
        # 创建邮件发送器
        sender = EmailSender()
        
        # 发送每周邮件
        success = sender.send_weekly_email()
        
        if success:
            logger.info("✅ 每周邮件发送成功")
        else:
            logger.error("❌ 每周邮件发送失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ 每周邮件发送异常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()