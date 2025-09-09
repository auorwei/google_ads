import sqlite3
import os
from datetime import datetime
from config import DATABASE_NAME


class AdDatabase:
    """Google广告数据库管理类"""
    
    def __init__(self):
        # 将相对路径转换为绝对路径，确保无论从哪个目录运行都能找到数据库
        if os.path.isabs(DATABASE_NAME):
            # 如果已经是绝对路径，直接使用
            self.db_path = DATABASE_NAME
        else:
            # 如果是相对路径，基于项目根目录计算绝对路径
            project_root = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(project_root, DATABASE_NAME)
        
        self.init_database()
    
    def init_database(self):
        """初始化数据库和表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建广告数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ads_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                country_code TEXT NOT NULL,
                ad_url TEXT,
                target_url TEXT,
                real_target_url TEXT,
                ref_parameter TEXT,
                ch_parameter TEXT,
                utm_campaign_parameter TEXT,
                ad_title TEXT,
                ad_description TEXT,
                position INTEGER,
                scrape_time TIMESTAMP NOT NULL,
                html_file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(keyword, country_code, ad_url, scrape_time)
            )
        ''')
        
        # 创建抓取日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scrape_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                country_code TEXT NOT NULL,
                status TEXT NOT NULL,
                ads_found INTEGER DEFAULT 0,
                error_message TEXT,
                scrape_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 检查并添加新字段（用于数据库迁移）
        self._migrate_database(cursor)
        
        conn.commit()
        conn.close()
    
    def _migrate_database(self, cursor):
        """数据库迁移，添加新字段"""
        try:
            # 检查是否需要添加real_target_url字段
            cursor.execute("PRAGMA table_info(ads_data)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'real_target_url' not in columns:
                cursor.execute('ALTER TABLE ads_data ADD COLUMN real_target_url TEXT')
                print("✅ 已添加 real_target_url 字段")
            
            if 'ref_parameter' not in columns:
                cursor.execute('ALTER TABLE ads_data ADD COLUMN ref_parameter TEXT')
                print("✅ 已添加 ref_parameter 字段")
            
            if 'ch_parameter' not in columns:
                cursor.execute('ALTER TABLE ads_data ADD COLUMN ch_parameter TEXT')
                print("✅ 已添加 ch_parameter 字段")
            
            if 'utm_campaign_parameter' not in columns:
                cursor.execute('ALTER TABLE ads_data ADD COLUMN utm_campaign_parameter TEXT')
                print("✅ 已添加 utm_campaign_parameter 字段")
                
        except Exception as e:
            print(f"数据库迁移时出错: {e}")
    
    def insert_ad_data(self, keyword, country_code, ad_data, scrape_time, html_file_path):
        """插入广告数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO ads_data 
                (keyword, country_code, ad_url, target_url, real_target_url, ref_parameter,
                 ch_parameter, utm_campaign_parameter, ad_title, ad_description, position, 
                 scrape_time, html_file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                keyword,
                country_code,
                ad_data.get('ad_url', ''),
                ad_data.get('target_url', ''),
                ad_data.get('real_target_url', ''),
                ad_data.get('ref_parameter', ''),
                ad_data.get('ch_parameter', ''),
                ad_data.get('utm_campaign_parameter', ''),
                ad_data.get('title', ''),
                ad_data.get('description', ''),
                ad_data.get('position', 0),
                scrape_time,
                html_file_path
            ))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"插入广告数据时出错: {e}")
            return None
        finally:
            conn.close()
    
    def insert_scrape_log(self, keyword, country_code, status, ads_found=0, error_message=None):
        """插入抓取日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO scrape_logs 
                (keyword, country_code, status, ads_found, error_message, scrape_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                keyword,
                country_code,
                status,
                ads_found,
                error_message,
                datetime.now()
            ))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"插入日志时出错: {e}")
            return None
        finally:
            conn.close()
    
    def get_ads_by_keyword(self, keyword, country_code=None):
        """根据关键词获取广告数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if country_code:
            cursor.execute('''
                SELECT * FROM ads_data 
                WHERE keyword = ? AND country_code = ?
                ORDER BY scrape_time DESC
            ''', (keyword, country_code))
        else:
            cursor.execute('''
                SELECT * FROM ads_data 
                WHERE keyword = ?
                ORDER BY scrape_time DESC
            ''', (keyword,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_scrape_stats(self):
        """获取抓取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总的抓取次数
        cursor.execute('SELECT COUNT(*) FROM scrape_logs')
        total_scrapes = cursor.fetchone()[0]
        
        # 成功抓取次数
        cursor.execute('SELECT COUNT(*) FROM scrape_logs WHERE status = "success"')
        successful_scrapes = cursor.fetchone()[0]
        
        # 总发现的广告数量
        cursor.execute('SELECT COUNT(*) FROM ads_data')
        total_ads = cursor.fetchone()[0]
        
        # 最近抓取时间
        cursor.execute('SELECT MAX(scrape_time) FROM scrape_logs')
        last_scrape = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_scrapes': total_scrapes,
            'successful_scrapes': successful_scrapes,
            'total_ads': total_ads,
            'last_scrape': last_scrape
        }