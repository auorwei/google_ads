import requests
import time
import os
from datetime import datetime
from urllib.parse import quote
from config import *
from database import AdDatabase
from ad_extractor import GoogleAdExtractor


class GoogleSERPScraper:
    """Google SERP数据抓取器"""
    
    def __init__(self):
        self.api_key = API_KEY
        self.zone = ZONE
        self.db = AdDatabase()
        self.ad_extractor = GoogleAdExtractor()
        self.session = requests.Session()
        
        # 确保HTML目录存在
        os.makedirs(HTML_DIR, exist_ok=True)
    
    def scrape_keyword_country(self, keyword, country_code):
        """抓取特定关键词在特定国家的SERP数据"""
        print(f"开始抓取关键词 '{keyword}' 在 {country_code} 的数据...")
        
        scrape_time = datetime.now()
        
        try:
            # 获取SERP数据
            html_content = self._fetch_serp_data(keyword, country_code)
            
            if not html_content:
                self.db.insert_scrape_log(
                    keyword, country_code, "failed", 
                    error_message="无法获取SERP数据"
                )
                return False
            
            # 保存HTML文件
            html_file_path = self._save_html_file(
                html_content, keyword, country_code, scrape_time
            )
            
            # 提取广告数据
            ads_data = self.ad_extractor.extract_ads(html_content)
            
            # 保存广告数据到数据库
            ads_saved = 0
            for ad_data in ads_data:
                if self.db.insert_ad_data(
                    keyword, country_code, ad_data, scrape_time, html_file_path
                ):
                    ads_saved += 1
            
            # 记录抓取日志
            self.db.insert_scrape_log(
                keyword, country_code, "success", ads_found=ads_saved
            )
            
            print(f"✅ 成功抓取 {ads_saved} 个广告")
            return True
            
        except Exception as e:
            error_msg = f"抓取失败: {str(e)}"
            print(f"❌ {error_msg}")
            self.db.insert_scrape_log(
                keyword, country_code, "failed", error_message=error_msg
            )
            return False
    
    def _fetch_serp_data(self, keyword, country_code):
        """使用Bright Data API获取SERP数据"""
        url = "https://api.brightdata.com/request"
        
        search_url = f"https://www.google.com/search?q={quote(keyword)}"
        
        payload = {
            "zone": self.zone,
            "url": search_url,
            "format": "json",
            "method": "GET",
            "country": country_code,
            "data_format": "html"
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 重试机制
        for attempt in range(MAX_RETRIES):
            try:
                print(f"  发送API请求 (尝试 {attempt + 1}/{MAX_RETRIES})...")
                
                response = self.session.post(
                    url, 
                    json=payload, 
                    headers=headers, 
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 根据实际API响应结构提取HTML内容
                    html_content = self._extract_html_from_response(result)
                    
                    if html_content:
                        print(f"  ✅ API请求成功，获得HTML内容 ({len(html_content)} 字符)")
                        return html_content
                    else:
                        print(f"  ⚠️ API响应中未找到HTML内容")
                        
                else:
                    print(f"  ❌ API请求失败: HTTP {response.status_code}")
                    print(f"  响应内容: {response.text[:500]}")
                
            except requests.exceptions.RequestException as e:
                print(f"  ❌ 请求异常: {str(e)}")
            
            # 如果不是最后一次尝试，等待一段时间后重试
            if attempt < MAX_RETRIES - 1:
                print(f"  等待 {RETRY_DELAY} 秒后重试...")
                time.sleep(RETRY_DELAY)
        
        return None
    
    def _extract_html_from_response(self, api_response):
        """从API响应中提取HTML内容"""
        # 这里需要根据实际的Bright Data API响应格式进行调整
        # 常见的响应格式可能包括：
        
        if isinstance(api_response, dict):
            # 尝试不同的可能的HTML字段名
            html_fields = ['html', 'body', 'content', 'data', 'page_content']
            
            for field in html_fields:
                if field in api_response:
                    content = api_response[field]
                    if isinstance(content, str) and len(content) > 100:
                        return content
            
            # 如果是嵌套结构
            if 'data' in api_response and isinstance(api_response['data'], dict):
                for field in html_fields:
                    if field in api_response['data']:
                        content = api_response['data'][field]
                        if isinstance(content, str) and len(content) > 100:
                            return content
        
        elif isinstance(api_response, str):
            # 如果响应直接就是HTML字符串
            if len(api_response) > 100:
                return api_response
        
        return None
    
    def _save_html_file(self, html_content, keyword, country_code, scrape_time):
        """保存HTML文件"""
        # 创建文件名，使用时间戳避免冲突
        timestamp = scrape_time.strftime("%Y%m%d_%H%M%S")
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_keyword = safe_keyword.replace(' ', '_')
        
        filename = f"{timestamp}_{country_code}_{safe_keyword}.html"
        file_path = os.path.join(HTML_DIR, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"  💾 HTML文件已保存: {filename}")
            return file_path
        except Exception as e:
            print(f"  ⚠️ 保存HTML文件失败: {str(e)}")
            return None
    
    def scrape_all_combinations(self):
        """抓取所有关键词和国家的组合"""
        total_combinations = len(KEYWORDS_LIST) * len(COUNTRY_LIST)
        current = 0
        successful = 0
        
        print(f"🚀 开始批量抓取，共 {total_combinations} 个组合")
        print(f"关键词数量: {len(KEYWORDS_LIST)}")
        print(f"国家数量: {len(COUNTRY_LIST)}")
        print("-" * 60)
        
        start_time = datetime.now()
        
        for keyword in KEYWORDS_LIST:
            for country_code in COUNTRY_LIST:
                current += 1
                
                print(f"\n[{current}/{total_combinations}] ", end="")
                
                success = self.scrape_keyword_country(keyword, country_code)
                if success:
                    successful += 1
                
                # 在请求之间添加延迟，避免被限制
                if current < total_combinations:
                    print(f"  ⏳ 等待 {RETRY_DELAY} 秒...")
                    time.sleep(RETRY_DELAY)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print(f"🎉 批量抓取完成!")
        print(f"总用时: {duration}")
        print(f"成功率: {successful}/{total_combinations} ({successful/total_combinations*100:.1f}%)")
        
        # 显示统计信息
        self.show_stats()
    
    def scrape_single(self, keyword, country_code):
        """抓取单个关键词和国家组合"""
        print(f"🎯 单次抓取模式")
        print(f"关键词: {keyword}")
        print(f"国家: {country_code}")
        print("-" * 40)
        
        success = self.scrape_keyword_country(keyword, country_code)
        
        if success:
            print(f"✅ 抓取完成")
        else:
            print(f"❌ 抓取失败")
        
        self.show_stats()
    
    def show_stats(self):
        """显示抓取统计信息"""
        stats = self.db.get_scrape_stats()
        
        print("\n📊 抓取统计:")
        print(f"  总抓取次数: {stats['total_scrapes']}")
        print(f"  成功次数: {stats['successful_scrapes']}")
        print(f"  发现的广告总数: {stats['total_ads']}")
        print(f"  最后抓取时间: {stats['last_scrape'] or '无'}")


if __name__ == "__main__":
    # 检查配置
    if API_KEY == "your_api_key_here" or ZONE == "your_zone_here":
        print("❌ 请先在 config.py 中配置 API_KEY 和 ZONE")
        exit(1)
    
    scraper = GoogleSERPScraper()
    
    # 可以选择运行模式
    import sys
    
    if len(sys.argv) == 3:
        # 单个关键词模式: python scraper.py "keyword" "country"
        keyword = sys.argv[1]
        country = sys.argv[2]
        scraper.scrape_single(keyword, country)
    else:
        # 批量模式
        scraper.scrape_all_combinations()