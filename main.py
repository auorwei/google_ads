#!/usr/bin/env python3
"""
Google SERP广告抓取工具
使用Bright Data API获取Google搜索结果页面，并提取广告信息
"""

import sys
import argparse
import traceback
from datetime import datetime
from scraper import GoogleSERPScraper
from database import AdDatabase
from email_sender import EmailSender
from config import KEYWORDS_LIST, COUNTRY_LIST, EMAIL_CONFIG
from logger import project_logger


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='Google SERP广告数据抓取工具')
    
    parser.add_argument(
        '--mode', 
        choices=['single', 'batch', 'stats'], 
        default='batch',
        help='运行模式: single(单次抓取), batch(批量抓取), stats(显示统计)'
    )
    
    parser.add_argument(
        '--keyword', 
        type=str, 
        help='要抓取的关键词 (single模式必需)'
    )
    
    parser.add_argument(
        '--country', 
        type=str, 
        help='目标国家代码 (single模式必需)'
    )
    
    parser.add_argument(
        '--list-config', 
        action='store_true',
        help='显示当前配置的关键词和国家列表'
    )
    
    parser.add_argument(
        '--export', 
        type=str,
        help='导出数据到CSV文件 (提供文件名)'
    )
    
    args = parser.parse_args()
    
    # 显示配置
    if args.list_config:
        show_config()
        return
    
    # 显示统计信息
    if args.mode == 'stats':
        show_stats()
        return
    
    # 导出数据
    if args.export:
        export_data(args.export)
        return
    
    # 创建抓取器
    scraper = GoogleSERPScraper()
    
    # 根据模式运行
    if args.mode == 'single':
        if not args.keyword or not args.country:
            print("❌ single模式需要提供 --keyword 和 --country 参数")
            print("示例: python main.py --mode single --keyword 'bingx' --country 'us'")
            return
        
        scraper.scrape_single(args.keyword, args.country)
        
        # 单次抓取完成后也发送邮件
       # send_scrape_result_email(scraper)
        
    elif args.mode == 'batch':
        print("🚀 批量抓取模式")
        print(f"将抓取 {len(KEYWORDS_LIST)} 个关键词 × {len(COUNTRY_LIST)} 个国家 = {len(KEYWORDS_LIST) * len(COUNTRY_LIST)} 个组合")
        
        # 询问用户确认
      #  confirm = input("是否继续? (y/n): ").lower().strip()
      #  if confirm != 'y':
      #      print("已取消")
      #ß      return
        
        scraper.scrape_all_combinations()
        
        # 抓取完成后自动发送邮件
       # send_scrape_result_email(scraper)


def show_config():
    """显示当前配置"""
    print("📋 当前配置:")
    print(f"关键词列表 ({len(KEYWORDS_LIST)} 个):")
    for i, keyword in enumerate(KEYWORDS_LIST, 1):
        print(f"  {i}. {keyword}")
    
    print(f"\n国家代码列表 ({len(COUNTRY_LIST)} 个):")
    for i, country in enumerate(COUNTRY_LIST, 1):
        print(f"  {i}. {country}")
    
    print(f"\n总抓取组合数: {len(KEYWORDS_LIST) * len(COUNTRY_LIST)}")


def show_stats():
    """显示统计信息"""
    db = AdDatabase()
    stats = db.get_scrape_stats()
    
    print("📊 数据库统计:")
    print(f"  总抓取次数: {stats['total_scrapes']}")
    print(f"  成功次数: {stats['successful_scrapes']}")
    print(f"  成功率: {stats['successful_scrapes'] / max(stats['total_scrapes'], 1) * 100:.1f}%")
    print(f"  发现的广告总数: {stats['total_ads']}")
    print(f"  最后抓取时间: {stats['last_scrape'] or '无'}")
    
    # 显示按关键词分组的统计
    print("\n📈 按关键词统计:")
    show_keyword_stats(db)


def show_keyword_stats(db):
    """显示按关键词分组的统计"""
    import sqlite3
    
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT keyword, COUNT(*) as ads_count, 
               COUNT(DISTINCT country_code) as countries_count
        FROM ads_data 
        GROUP BY keyword
        ORDER BY ads_count DESC
    ''')
    
    results = cursor.fetchall()
    
    if results:
        for keyword, ads_count, countries_count in results:
            print(f"  {keyword}: {ads_count} 个广告 (覆盖 {countries_count} 个国家)")
    else:
        print("  暂无数据")
    
    conn.close()


def export_data(filename):
    """导出数据到CSV文件"""
    import csv
    import sqlite3
    from database import AdDatabase
    
    db = AdDatabase()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT keyword, country_code, ad_title, ad_url, target_url, 
               real_target_url, ref_parameter, ch_parameter, utm_campaign_parameter,
               ad_description, position, scrape_time
        FROM ads_data
        ORDER BY scrape_time DESC, keyword, country_code, position
    ''')
    
    results = cursor.fetchall()
    
    if not results:
        print("❌ 数据库中没有数据可导出")
        return
    
    # 确保文件名有.csv扩展名
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            # 写入表头
            writer.writerow([
                '关键词', '国家代码', '广告标题', '广告URL', 
                '目标URL', '真实目标URL', 'Ref参数', 'Ch参数', 'UTM Campaign参数',
                '广告描述', '位置', '抓取时间'
            ])
            
            # 写入数据
            writer.writerows(results)
        
        print(f"✅ 数据已导出到 {filename}")
        print(f"   共导出 {len(results)} 条记录")
        
    except Exception as e:
        print(f"❌ 导出失败: {str(e)}")
    
    conn.close()


def send_scrape_result_email(scraper):
    """发送抓取结果邮件到272363364@qq.com"""
    logger = project_logger.get_logger('main_email', 'main_email.log')
    
    try:
        logger.info("🚀 开始发送抓取结果邮件")
        
        # 创建邮件发送器
        email_sender = EmailSender()
        
        # 获取统计信息
        stats = scraper.db.get_scrape_stats()
        
        # 构建邮件主题
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"[抓取完成] Google广告数据抓取结果 - {current_time}"
        
        # 发送邮件给272363364@qq.com
        recipients = ["272363364@qq.com"]
        
        success = email_sender.send_email(
            subject=subject,
            recipients=recipients
        )
        
        if success:
            logger.info(f"✅ 抓取结果邮件发送成功: {', '.join(recipients)}")
            print(f"📧 抓取结果邮件已发送到: {', '.join(recipients)}")
        else:
            logger.error("❌ 抓取结果邮件发送失败")
            print("❌ 抓取结果邮件发送失败")
            
    except Exception as e:
        logger.error(f"❌ 发送抓取结果邮件异常: {str(e)}")
        print(f"❌ 发送抓取结果邮件失败: {str(e)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断程序")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序异常: {str(e)}")
        traceback.print_exc()
        sys.exit(1)