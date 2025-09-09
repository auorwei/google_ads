#!/usr/bin/env python3
"""
Ref参数统计脚本
从数据库统计今日和过去8天分别抓取到的ref去重，并输出这些ref code
"""

import sys
import os
import sqlite3
from datetime import datetime, timedelta

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_NAME
from logger import project_logger

class RefStatsAnalyzer:
    """Ref参数统计分析器"""
    
    def __init__(self):
        self.db_path = DATABASE_NAME
        self.logger = project_logger.get_logger('ref_stats', 'ref_stats.log')
    
    def get_today_refs(self):
        """获取今日新发现的ref参数（当日00:00到现在）"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now()
        
        return self._get_refs_by_date_range(today_start, today_end, "今日")
    
    def get_past_8_days_refs(self):
        """获取过去8天的ref参数（8天前到现在）"""
        now = datetime.now()
        eight_days_ago = now - timedelta(days=8)
        
        return self._get_refs_by_date_range(eight_days_ago, now, "过去8天")
    
    def get_past_24_hours_refs(self):
        """获取过去24小时的ref参数"""
        now = datetime.now()
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        return self._get_refs_by_date_range(twenty_four_hours_ago, now, "过去24小时")
    
    def _get_refs_by_date_range(self, start_date, end_date, period_name):
        """根据日期范围获取ref参数统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查询指定时间范围内的唯一ref参数，按首次发现时间排序
            cursor.execute('''
                SELECT 
                    ref_parameter,
                    keyword,
                    MIN(scrape_time) as first_discovered,
                    real_target_url,
                    ad_title,
                    country_code,
                    COUNT(*) as occurrence_count
                FROM ads_data 
                WHERE scrape_time >= ? AND scrape_time <= ?
                AND ref_parameter IS NOT NULL 
                AND ref_parameter != ''
                GROUP BY ref_parameter
                ORDER BY first_discovered DESC
            ''', (start_date, end_date))
            
            results = cursor.fetchall()
            
            # 构建统计信息
            stats = {
                'period': period_name,
                'start_date': start_date,
                'end_date': end_date,
                'total_unique_refs': len(results),
                'refs_data': results
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"查询{period_name}数据失败: {str(e)}")
            return None
        finally:
            conn.close()
    
    def format_country_name(self, code):
        """格式化国家名称"""
        country_map = {
            'in': '印度',
            'de': '德国', 
            'tw': '中国台湾',
            'ru': '俄罗斯',
            'es': '西班牙',
            'us': '美国',
            'uk': '英国',
            'ca': '加拿大',
            'au': '澳大利亚',
            'jp': '日本',
            'kr': '韩国',
            'sg': '新加坡',
            'hk': '香港',
            'fr': '法国',
            'it': '意大利'
        }
        return country_map.get(code, code.upper())
    
    def print_refs_summary(self, stats):
        """打印ref统计摘要"""
        if not stats or not stats['refs_data']:
            print(f"\n📭 {stats['period']}无数据")
            return
        
        period = stats['period']
        total_refs = stats['total_unique_refs']
        start_str = stats['start_date'].strftime('%Y-%m-%d %H:%M:%S')
        end_str = stats['end_date'].strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n" + "="*60)
        print(f"📊 {period}统计报告")
        print(f"📅 时间范围: {start_str} ~ {end_str}")
        print(f"🎯 唯一Ref参数数量: {total_refs} 个")
        print("="*60)
        
        # 输出所有ref参数
        print(f"\n📋 {period}发现的所有Ref参数:")
        print("-"*60)
        
        for i, (ref_param, keyword, first_discovered, real_url, title, country, count) in enumerate(stats['refs_data'], 1):
            # 格式化时间
            try:
                discovered_time = datetime.fromisoformat(first_discovered.replace('Z', '+00:00'))
                time_str = discovered_time.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = first_discovered
            
            country_name = self.format_country_name(country)
            title = title or '无标题'
            
            print(f"{i:2d}. {ref_param}")
            print(f"     关键词: {keyword}")
            print(f"     首次发现: {time_str}")
            print(f"     国家: {country_name}")
            print(f"     标题: {title}")
            print(f"     出现次数: {count}")
            if real_url:
                print(f"     链接: {real_url}")
            print()
    
    def print_refs_list_only(self, stats):
        """只打印ref列表（简洁版）"""
        if not stats or not stats['refs_data']:
            print(f"{stats['period']}: 无数据")
            return
        
        period = stats['period']
        refs = [row[0] for row in stats['refs_data']]
        
        print(f"\n🎯 {period}发现的Ref参数 ({len(refs)}个):")
        print(", ".join(refs))
    
    def export_refs_to_file(self, stats, filename):
        """导出ref参数到文件"""
        if not stats or not stats['refs_data']:
            print(f"❌ {stats['period']}无数据可导出")
            return False
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {stats['period']}发现的Ref参数统计\n")
                f.write(f"# 时间范围: {stats['start_date'].strftime('%Y-%m-%d %H:%M:%S')} ~ {stats['end_date'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 唯一Ref参数数量: {stats['total_unique_refs']} 个\n")
                f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for ref_param, keyword, first_discovered, real_url, title, country, count in stats['refs_data']:
                    f.write(f"{ref_param}\n")
            
            print(f"✅ {stats['period']}的Ref参数已导出到: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ 导出失败: {str(e)}")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ref参数统计分析工具')
    
    parser.add_argument(
        '--mode',
        choices=['summary', 'list', 'export', 'all'],
        default='summary',
        help='输出模式: summary(详细报告), list(简洁列表), export(导出文件), all(全部)'
    )
    
    parser.add_argument(
        '--period',
        choices=['today', '24hours', '8days', 'all'],
        default='all',
        help='时间范围: today(今日), 24hours(过去24小时), 8days(过去8天), all(全部)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='导出文件的目录路径'
    )
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = RefStatsAnalyzer()
    
    print("🚀 开始分析Ref参数统计...")
    
    # 获取数据
    stats_data = {}
    
    if args.period in ['today', 'all']:
        stats_data['today'] = analyzer.get_today_refs()
    
    if args.period in ['24hours', 'all']:
        stats_data['24hours'] = analyzer.get_past_24_hours_refs()
    
    if args.period in ['8days', 'all']:
        stats_data['8days'] = analyzer.get_past_8_days_refs()
    
    # 输出结果
    for period_key, stats in stats_data.items():
        if not stats:
            continue
        
        if args.mode in ['summary', 'all']:
            analyzer.print_refs_summary(stats)
        
        if args.mode in ['list', 'all']:
            analyzer.print_refs_list_only(stats)
        
        if args.mode in ['export', 'all']:
            filename = os.path.join(args.output_dir, f"refs_{period_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            analyzer.export_refs_to_file(stats, filename)
    
    print("\n🎉 分析完成!")

if __name__ == "__main__":
    main()