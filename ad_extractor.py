import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote


class GoogleAdExtractor:
    """Google SERP广告数据提取器"""
    
    def __init__(self):
        # 初始化HTTP会话，用于获取真实目标URL
        self.session = requests.Session()
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
    
    def extract_ads(self, html_content, get_real_urls=True):
        """从HTML内容中提取广告数据"""
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        ads_data = self._extract_ads_by_data_rw(soup)
        
        # 如果需要，获取真实的目标URL和ref参数
        if get_real_urls:
            self._enrich_ads_with_real_urls(ads_data)
        
        return ads_data
    
    def _extract_ads_by_data_rw(self, soup):
        """使用data-rw属性提取广告"""
        ads = []
        
        # 查找所有带有data-rw属性的a标签
        ad_links = soup.find_all('a', {'data-rw': True})
        
        for i, link in enumerate(ad_links, 1):
            try:
                # 获取广告URL (data-rw属性值)
                ad_url = link.get('data-rw', '')
                if not ad_url:
                    continue
                
                # 从URL参数中解析目标URL
                target_url = self._extract_target_url_from_ad_url(ad_url)
                
                # 查找广告标题
                title = self._extract_title_from_ad_element(link)
                
                # 查找广告描述
                description = self._extract_description_from_ad_element(link)
                
                # 验证这是否是有效广告
                if self._is_valid_ad_data(title, ad_url, target_url):
                    ads.append({
                        'type': 'data_rw_ad',
                        'title': title,
                        'ad_url': ad_url,
                        'target_url': target_url,
                        'description': description,
                        'position': i
                    })
            except Exception:
                continue
        
        return ads
    
    def _extract_target_url_from_ad_url(self, ad_url):
        """从Google广告URL中提取真实的目标URL"""
        if not ad_url:
            return ""
        
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
            
            return ""
            
        except Exception:
            return ""
    
    def _extract_title_from_ad_element(self, link_element):
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
        
        return ""
    
    def _extract_description_from_ad_element(self, link_element):
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
        
        return ""
    
    def _is_valid_ad_data(self, title, ad_url, target_url):
        """验证广告数据是否有效"""
        # 必须有标题或有效的URL
        if not title or len(title.strip()) < 3:
            if not ad_url:
                return False
        
        # 必须有广告URL
        if not ad_url:
            return False
        
        return True
    
    def _enrich_ads_with_real_urls(self, ads_data):
        """为广告数据添加真实的目标URL和ref参数"""
        for ad in ads_data:
            if ad.get('ad_url'):
                real_target_result = self._get_real_target_url(ad['ad_url'])
                if real_target_result:
                    ad['real_target_url'] = real_target_result['final_url']
                    if real_target_result['ref_parameter']:
                        ad['ref_parameter'] = real_target_result['ref_parameter']
                    if real_target_result['ch_parameter']:
                        ad['ch_parameter'] = real_target_result['ch_parameter']
                    if real_target_result['utm_campaign_parameter']:
                        ad['utm_campaign_parameter'] = real_target_result['utm_campaign_parameter']
    
    def _get_real_target_url(self, ad_url):
        """访问广告URL获取真实的目标地址"""
        try:
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
            
            # 提取URL中的各种参数
            ref_value = self._extract_ref_parameter(final_url)
            ch_value = self._extract_ch_parameter(final_url)
            utm_campaign_value = self._extract_utm_campaign_parameter(final_url)
            
            return {
                'final_url': final_url,
                'ref_parameter': ref_value,
                'ch_parameter': ch_value,
                'utm_campaign_parameter': utm_campaign_value
            }
                
        except Exception:
            return None
    
    def _extract_ref_parameter(self, url):
        """从URL中提取ref参数"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # 只查找确切的ref参数
            if 'ref' in query_params:
                ref_value = query_params['ref'][0]
                if ref_value:
                    return ref_value
            
            return None
            
        except Exception:
            return None
    
    def _extract_ch_parameter(self, url):
        """从URL中提取ch参数"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # 只查找确切的ch参数
            if 'ch' in query_params:
                ch_value = query_params['ch'][0]
                if ch_value:
                    return ch_value
            
            return None
            
        except Exception:
            return None
    
    def _extract_utm_campaign_parameter(self, url):
        """从URL中提取utm_campaign参数"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # 只查找确切的utm_campaign参数
            if 'utm_campaign' in query_params:
                utm_campaign_value = query_params['utm_campaign'][0]
                if utm_campaign_value:
                    return utm_campaign_value
            
            return None
            
        except Exception:
            return None