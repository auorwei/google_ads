#!/usr/bin/env python3
"""
每小时监控脚本
运行广告抓取任务
"""

import sys
import os
from datetime import datetime

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import GoogleSERPScraper
from config import KEYWORDS_LIST, COUNTRY_LIST

# 导入日志系统
from logger import project_logger

def main():
    """主监控函数"""
    logger = project_logger.get_hourly_logger()
    
    start_time = datetime.now()
    logger.info("🕐 开始每小时监控任务")
    logger.info(f"监控关键词: {KEYWORDS_LIST}")
    logger.info(f"监控国家: {COUNTRY_LIST}")
    
    try:
        # 创建抓取器
        scraper = GoogleSERPScraper()
        
        # 执行抓取
        scraper.scrape_all_combinations()
        
        # 显示统计信息
        stats = scraper.db.get_scrape_stats()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("✅ 监控任务完成")
        logger.info(f"用时: {duration}")
        logger.info(f"总广告数: {stats['total_ads']}")
        logger.info(f"最后抓取: {stats['last_scrape']}")
        
    except Exception as e:
        logger.error(f"❌ 监控任务失败: {str(e)}")
        raise

if __name__ == "__main__":
    main()