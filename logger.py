#!/usr/bin/env python3
"""
统一日志系统
为项目中的所有模块提供统一的日志配置
"""

import logging
import logging.handlers
import os
from datetime import datetime


class ProjectLogger:
    """项目日志管理器"""
    
    def __init__(self, logs_dir="logs"):
        """
        初始化日志系统
        
        Args:
            logs_dir: 日志目录路径
        """
        self.logs_dir = logs_dir
        self._ensure_logs_dir()
        
    def _ensure_logs_dir(self):
        """确保日志目录存在"""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
    
    def get_logger(self, name, log_file=None, level=logging.INFO, console=True):
        """
        获取配置好的日志器
        
        Args:
            name: 日志器名称
            log_file: 日志文件名（不含路径）
            level: 日志级别
            console: 是否输出到控制台
            
        Returns:
            配置好的logger对象
        """
        logger = logging.getLogger(name)
        
        # 如果logger已经有handlers，说明已经配置过了
        if logger.handlers:
            return logger
            
        logger.setLevel(level)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器（如果指定了日志文件）
        if log_file:
            file_path = os.path.join(self.logs_dir, log_file)
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # 控制台处理器
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def get_scraper_logger(self):
        """获取爬虫日志器"""
        return self.get_logger('scraper', 'scraper.log')
    
    def get_email_logger(self):
        """获取邮件日志器"""
        return self.get_logger('email', 'email.log')
    
    def get_scheduler_logger(self):
        """获取调度器日志器"""
        return self.get_logger('scheduler', 'scheduler.log')
    
    def get_hourly_logger(self):
        """获取每小时监控日志器"""
        return self.get_logger('hourly_monitor', 'hourly.log')
    
    def get_daily_email_logger(self):
        """获取每日邮件日志器"""
        return self.get_logger('daily_email', 'daily_email.log')
    
    def get_weekly_email_logger(self):
        """获取每周邮件日志器"""
        return self.get_logger('weekly_email', 'weekly_email.log')


# 全局日志管理器实例
project_logger = ProjectLogger()


def get_logger(name, log_file=None, level=logging.INFO, console=True):
    """
    快捷获取日志器的函数
    
    Args:
        name: 日志器名称
        log_file: 日志文件名
        level: 日志级别
        console: 是否输出到控制台
        
    Returns:
        配置好的logger对象
    """
    return project_logger.get_logger(name, log_file, level, console)


if __name__ == "__main__":
    # 测试日志系统
    logger = get_logger('test', 'test.log')
    
    logger.info("日志系统测试开始")
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.info("日志系统测试完成")
    
    print(f"测试日志已写入: {os.path.abspath('logs/test.log')}")