#!/usr/bin/env python3
"""
广告解析测试代码
使用新的解析方法测试现有HTML文件中的广告提取效果
"""

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import parse_qs, urlparse, unquote
import re


class TestAdParser:
    """测试广告解析器"""
    
    def __init__(self):
        self.session = requests.Session()
        # 设置完整的请求头模拟真实浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        })
    
    def parse_html_file(self, file_path):
        """解析单个HTML文件"""
        print(f"\n🔍 解析文件: {os.path.basename(file_path)}")
        print("=" * 60)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        ads = self.extract_ads_with_data_rw(soup)
        
        print(f"📊 找到 {len(ads)} 个广告")
        
        for i, ad in enumerate(ads, 1):
            print(f"\n📢 广告 #{i}")
            print(f"   标题: {ad.get('title', '无')}")
            print(f"   广告URL: {ad.get('ad_url', '无')[:100]}...")
            print(f"   目标URL: {ad.get('target_url', '无')}")
            print(f"   描述: {ad.get('description', '无')}")
            
            # 访问广告URL获取真实的目标地址
            if ad.get('ad_url'):
                print(f"   🔄 正在访问广告URL获取真实目标地址...")
                real_target_result = self.get_real_target_url(ad['ad_url'])
                if real_target_result:
                    print(f"   ✅ 真实目标URL: {real_target_result['final_url']}")
                    if real_target_result['ref_parameter']:
                        print(f"   🎯 Ref参数: {real_target_result['ref_parameter']}")
                        ad['ref_parameter'] = real_target_result['ref_parameter']
                    ad['real_target_url'] = real_target_result['final_url']
                else:
                    print(f"   ❌ 无法获取真实目标URL")
        
        return ads
    
    def extract_ads_with_data_rw(self, soup):
        """使用data-rw属性提取广告"""
        ads = []
        
        # 查找所有带有data-rw属性的a标签
        ad_links = soup.find_all('a', {'data-rw': True})
        
        print(f"🎯 找到 {len(ad_links)} 个带有data-rw属性的链接")
        
        for i, link in enumerate(ad_links, 1):
            print(f"\n分析链接 #{i}:")
            
            # 获取广告URL (data-rw属性值)
            ad_url = link.get('data-rw', '')
            print(f"  data-rw: {ad_url[:80]}...")
            
            # 解析目标URL
            target_url = self.extract_target_url_from_ad_url(ad_url)
            print(f"  解析的目标URL: {target_url}")
            
            # 查找广告标题
            title = self.extract_title_from_ad_element(link)
            print(f"  标题: {title}")
            
            # 查找广告描述
            description = self.extract_description_from_ad_element(link)
            print(f"  描述: {description}")
            
            # 验证这是否是有效广告
            if self.is_valid_ad_data(title, ad_url, target_url):
                ads.append({
                    'title': title,
                    'ad_url': ad_url,
                    'target_url': target_url,
                    'description': description,
                    'position': i
                })
                print(f"  ✅ 有效广告")
            else:
                print(f"  ❌ 无效广告，跳过")
        
        return ads
    
    def extract_target_url_from_ad_url(self, ad_url):
        """从Google广告URL中提取真实的目标URL"""
        if not ad_url:
            return "无"
        
        try:
            # Google广告URL通常包含多个参数，真实URL可能在不同参数中
            parsed_url = urlparse(ad_url)
            query_params = parse_qs(parsed_url.query)
            
            # 常见的目标URL参数名
            url_param_names = ['url', 'adurl', 'q', 'dest_url', 'continue']
            
            for param_name in url_param_names:
                if param_name in query_params:
                    target_url = query_params[param_name][0]
                    if target_url.startswith('http'):
                        return unquote(target_url)
            
            # 如果在查询参数中没找到，尝试在URL路径中查找
            # 有时目标URL直接编码在路径中
            url_patterns = [
                r'url=([^&]+)',
                r'adurl=([^&]+)',
                r'dest_url=([^&]+)'
            ]
            
            for pattern in url_patterns:
                match = re.search(pattern, ad_url)
                if match:
                    target_url = unquote(match.group(1))
                    if target_url.startswith('http'):
                        return target_url
            
            return "无法解析"
            
        except Exception as e:
            print(f"    解析URL时出错: {e}")
            return "解析出错"
    
    def extract_title_from_ad_element(self, link_element):
        """从广告元素中提取标题"""
        # 先在链接本身中查找标题
        title_selectors = [
            # 直接子元素中的标题
            'div[role="heading"]',
            'h1', 'h2', 'h3', 'h4',
            # 常见的Google广告标题类
            '.CCgQ5', '.vCa9Yd', '.QfkTvb', '.MBeuO', '.Va3FIb',
            # 其他可能的标题容器
            '[aria-level="3"]',
            'span'
        ]
        
        for selector in title_selectors:
            title_elem = link_element.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text().strip()
                if title_text and len(title_text) > 3:
                    return title_text
        
        # 如果在链接内没找到，向上查找父容器
        parent = link_element.parent
        for _ in range(3):  # 最多向上查找3层
            if not parent:
                break
            
            for selector in title_selectors:
                title_elem = parent.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text().strip()
                    if title_text and len(title_text) > 3:
                        return title_text
            
            parent = parent.parent
        
        # 最后尝试使用链接的直接文本内容
        link_text = link_element.get_text().strip()
        if link_text and len(link_text) > 3:
            return link_text
        
        return "无标题"
    
    def extract_description_from_ad_element(self, link_element):
        """从广告元素中提取描述"""
        # 描述通常在广告容器中，但不是标题
        desc_selectors = [
            '.VwiC3b', '.yXK7lf', '.s3v9rd', '.st', '.IsZvec',
            '.BNeawe', '.UPmit'
        ]
        
        # 在当前元素中查找
        for selector in desc_selectors:
            desc_elem = link_element.select_one(selector)
            if desc_elem:
                desc_text = desc_elem.get_text().strip()
                if desc_text and len(desc_text) > 10:
                    return desc_text
        
        # 在父容器中查找
        parent = link_element.parent
        for _ in range(3):
            if not parent:
                break
            
            for selector in desc_selectors:
                desc_elem = parent.select_one(selector)
                if desc_elem:
                    desc_text = desc_elem.get_text().strip()
                    if desc_text and len(desc_text) > 10:
                        return desc_text
            
            parent = parent.parent
        
        return "无描述"
    
    def is_valid_ad_data(self, title, ad_url, target_url):
        """验证广告数据是否有效"""
        # 必须有标题或有效的URL
        if not title or title == "无标题":
            if not ad_url:
                return False
        
        # 标题不能太短
        if title and title != "无标题" and len(title.strip()) < 3:
            return False
        
        # 必须有广告URL
        if not ad_url:
            return False
        
        return True
    
    def get_real_target_url(self, ad_url):
        """访问广告URL获取真实的目标地址"""
        try:
            print(f"      访问: {ad_url[:80]}...")
            
            # 使用GET请求访问广告URL，允许重定向
            # 添加Referer头来模拟从Google搜索页面点击
            headers = {
                'Referer': 'https://www.google.com/',
                'Cache-Control': 'max-age=0'
            }
            
            response = self.session.get(
                ad_url,
                allow_redirects=True,
                timeout=15,
                headers=headers
            )
            
            final_url = response.url
            print(f"      状态码: {response.status_code}")
            print(f"      最终URL: {final_url[:80]}...")
            
            # 提取URL中的ref参数
            ref_value = self.extract_ref_parameter(final_url)
            if ref_value:
                print(f"      🎯 提取到ref参数: {ref_value}")
            else:
                print(f"      ⚠️ 未找到ref参数")
            
            # 检查是否是有效的目标网站
            if self.is_valid_target_url(final_url):
                result = {
                    'final_url': final_url,
                    'ref_parameter': ref_value
                }
                return result
            else:
                print(f"      ⚠️ 可能不是有效的目标URL")
                result = {
                    'final_url': final_url,
                    'ref_parameter': ref_value
                }
                return result  # 仍然返回，让用户判断
                
        except requests.exceptions.Timeout:
            print(f"      ⏰ 请求超时")
            return None
        except requests.exceptions.RequestException as e:
            print(f"      ❌ 请求失败: {e}")
            return None
        except Exception as e:
            print(f"      ❌ 获取真实URL时出错: {e}")
            return None
    
    def extract_ref_parameter(self, url):
        """从URL中提取ref参数"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # 查找ref参数，可能有不同的形式
            ref_param_names = ['ref', 'referrer', 'reference', 'utm_source', 'source']
            
            for param_name in ref_param_names:
                if param_name in query_params:
                    ref_value = query_params[param_name][0]
                    if ref_value:
                        return ref_value
            
            return None
            
        except Exception as e:
            print(f"      提取ref参数时出错: {e}")
            return None
    
    def is_valid_target_url(self, url):
        """检查是否是有效的目标URL"""
        if not url:
            return False
        
        # 排除明显不是目标网站的URL
        invalid_domains = [
            'google.com', 'googleadservices.com', 'googlesyndication.com',
            'doubleclick.net', 'googletagmanager.com'
        ]
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        for invalid_domain in invalid_domains:
            if invalid_domain in domain:
                return False
        
        return True


def main():
    """主测试函数"""
    parser = TestAdParser()
    
    # 查找htmls目录中的所有HTML文件
    html_dir = "htmls"
    if not os.path.exists(html_dir):
        print(f"❌ {html_dir} 目录不存在")
        return
    
    html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
    
    if not html_files:
        print(f"❌ {html_dir} 目录中没有HTML文件")
        return
    
    print(f"🚀 开始测试广告解析")
    print(f"发现 {len(html_files)} 个HTML文件")
    
    total_ads = 0
    
    for html_file in html_files:
        file_path = os.path.join(html_dir, html_file)
        ads = parser.parse_html_file(file_path)
        total_ads += len(ads)
    
    print(f"\n🎉 测试完成！")
    print(f"总计发现 {total_ads} 个广告")
    
    if total_ads > 0:
        print(f"\n✅ 解析方法有效，建议继续优化主代码")
    else:
        print(f"\n⚠️ 未发现广告，可能需要调整解析策略")


if __name__ == "__main__":
    main()