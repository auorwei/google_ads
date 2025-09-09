#!/usr/bin/env python3
"""
邮件发送模块
从数据库中提取最近8天的广告信息，按ref去重后发送邮件报告
"""

import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from config import EMAIL_CONFIG, DATABASE_NAME
from database import AdDatabase


class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        self.db = AdDatabase()
        self.email_config = EMAIL_CONFIG
    
    def get_recent_ads_data(self, days=8):
        """获取最近N天的广告数据，按ref去重"""
        return self.get_ads_data_by_date_range(days=days)
    
    def get_ads_data_by_date_range(self, days=8, start_date=None, end_date=None):
        """
        根据日期范围获取广告数据，按ref去重
        
        Args:
            days: 最近N天的数据（当start_date和end_date都为None时使用）
            start_date: 开始日期（datetime对象）
            end_date: 结束日期（datetime对象）
        """
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # 确定查询的时间范围
        if start_date and end_date:
            # 使用指定的日期范围
            query_start = start_date
            query_end = end_date
        elif start_date:
            # 只指定了开始日期，到当前时间
            query_start = start_date
            query_end = datetime.now()
        else:
            # 使用days参数，计算N天前的日期
            query_start = datetime.now() - timedelta(days=days)
            query_end = datetime.now()
        
        # 查询指定时间范围的数据，按ref分组，取每个ref的最早记录
        cursor.execute('''
            SELECT 
                ref_parameter,
                keyword,
                MIN(scrape_time) as first_discovered,
                real_target_url,
                ad_title,
                country_code,
                ch_parameter,
                utm_campaign_parameter
            FROM ads_data 
            WHERE scrape_time >= ? AND scrape_time <= ?
            AND ref_parameter IS NOT NULL 
            AND ref_parameter != ''
            GROUP BY ref_parameter
            ORDER BY first_discovered DESC
        ''', (query_start, query_end))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_today_ads_data(self):
        """获取过去24小时内新发现的广告数据"""
        now = datetime.now()
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        return self.get_ads_data_by_date_range(start_date=twenty_four_hours_ago, end_date=now)
    
    def format_email_content(self, ads_data):
        """格式化邮件内容"""
        if not ads_data:
            return self._create_empty_report()
        
        # 统计信息
        total_refs = len(ads_data)
        date_range = f"{datetime.now().strftime('%Y-%m-%d')} (最近8天)"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #1976d2; border-bottom: 2px solid #1976d2; padding-bottom: 10px; }}
        .ref-list {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .ref-item {{ display: inline-block; margin: 5px; padding: 8px 12px; background-color: #2196f3; color: white; border-radius: 3px; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .url-link {{ max-width: 300px; word-break: break-all; }}
        .timestamp {{ color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Google广告监控报告</h1>
        <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>数据范围: {date_range}</p>
    </div>
    
    <div class="summary">
        <h3>📊 统计摘要</h3>
        <p><strong>发现的唯一Ref参数数量:</strong> {total_refs} 个</p>
        <p><strong>监控关键词:</strong> bingx, bingx exchange</p>
        <p><strong>监控国家:</strong> 印度, 德国, 中国台湾, 俄罗斯, 西班牙</p>
    </div>

    <div class="section">
        <h2>📋 第一部分：去重后的Ref参数列表</h2>
        <div class="ref-list">
"""
        
        # 第一部分：只展示去重后的ref
        for row in ads_data:
            ref_param = row[0]
            html_content += f'            <span class="ref-item">{ref_param}</span>\n'
        
        html_content += """        </div>
    </div>

    <div class="section">
        <h2>📝 第二部分：详细信息</h2>
        <table>
            <thead>
                <tr>
                    <th>Ref参数</th>
                    <th>搜索关键词</th>
                    <th>首次发现时间</th>
                    <th>真实链接</th>
                    <th>广告标题</th>
                    <th>国家</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # 第二部分：详细信息表格
        for row in ads_data:
            ref_param, keyword, first_discovered, real_url, title, country, ch_param, utm_campaign = row
            
            # 格式化时间
            try:
                discovered_time = datetime.fromisoformat(first_discovered.replace('Z', '+00:00'))
                formatted_time = discovered_time.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_time = first_discovered
            
            # 处理可能的空值
            real_url = real_url or '无'
            title = title or '无标题'
            country_name = self._get_country_name(country)
            
            html_content += f"""                <tr>
                    <td><code>{ref_param}</code></td>
                    <td><strong>{keyword}</strong></td>
                    <td class="timestamp">{formatted_time}</td>
                    <td class="url-link">
                        <a href="{real_url}" target="_blank" title="{real_url}">链接</a>
                    </td>
                    <td>{title}</td>
                    <td>{country_name}</td>
                </tr>
"""
        
        html_content += """            </tbody>
        </table>
    </div>

    <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; color: #666; font-size: 12px;">
        <p>💡 说明：</p>
        <ul>
            <li>本报告包含最近8天内发现的所有唯一Ref参数</li>
            <li>每个Ref参数只显示首次发现的记录</li>
            <li>点击真实链接可直接访问目标网站</li>
            <li>此邮件由Google广告监控系统自动生成</li>
        </ul>
    </div>

</body>
</html>
"""
        
        return html_content
    
    def format_daily_email_content(self, ads_data, report_date):
        """格式化每日邮件内容 - 专门用于过去24小时新发现的ref参数"""
        if not ads_data:
            return self._create_empty_daily_report(report_date)
        
        # 统计信息
        total_refs = len(ads_data)
        current_time = datetime.now()
        twenty_four_hours_ago = current_time - timedelta(hours=24)
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #28a745; border-bottom: 2px solid #28a745; padding-bottom: 10px; }}
        .ref-list {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .ref-item {{ display: inline-block; margin: 5px; padding: 8px 12px; background-color: #28a745; color: white; border-radius: 3px; font-size: 12px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .url-link {{ max-width: 300px; word-break: break-all; }}
        .timestamp {{ color: #666; font-size: 12px; }}
        .daily-badge {{ background-color: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📅 每日Google广告监控报告</h1>
        <p>报告日期: <strong>{report_date}</strong></p>
        <p>报告生成时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><span class="daily-badge">过去24小时新发现</span></p>
    </div>
    
    <div class="summary">
        <h3>📊 24小时统计摘要</h3>
        <p><strong>过去24小时新发现的唯一Ref参数数量:</strong> {total_refs} 个</p>
        <p><strong>监控关键词:</strong> bingx, bingx exchange</p>
        <p><strong>监控国家:</strong> 印度, 德国, 中国台湾, 俄罗斯, 西班牙</p>
        <p><strong>数据时间范围:</strong> {twenty_four_hours_ago.strftime('%Y-%m-%d %H:%M')} ~ {current_time.strftime('%Y-%m-%d %H:%M')}</p>
    </div>

    <div class="section">
        <h2>📋 第一部分：过去24小时新发现的Ref参数列表</h2>
        <div class="ref-list">
"""
        
        # 第一部分：只展示当日新发现的ref
        for row in ads_data:
            ref_param = row[0]
            html_content += f'            <span class="ref-item">{ref_param}</span>\n'
        
        html_content += """        </div>
    </div>

    <div class="section">
        <h2>📝 第二部分：详细信息</h2>
        <table>
            <thead>
                <tr>
                    <th>Ref参数</th>
                    <th>搜索关键词</th>
                    <th>首次发现时间</th>
                    <th>真实链接</th>
                    <th>广告标题</th>
                    <th>国家</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # 第二部分：详细信息表格
        for row in ads_data:
            ref_param, keyword, first_discovered, real_url, title, country, ch_param, utm_campaign = row
            
            # 格式化时间
            try:
                discovered_time = datetime.fromisoformat(first_discovered.replace('Z', '+00:00'))
                formatted_time = discovered_time.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_time = first_discovered
            
            # 处理可能的空值
            real_url = real_url or '无'
            title = title or '无标题'
            country_name = self._get_country_name(country)
            
            html_content += f"""                <tr>
                    <td><code>{ref_param}</code></td>
                    <td><strong>{keyword}</strong></td>
                    <td class="timestamp">{formatted_time}</td>
                    <td class="url-link">
                        <a href="{real_url}" target="_blank" title="{real_url}">链接</a>
                    </td>
                    <td>{title}</td>
                    <td>{country_name}</td>
                </tr>
"""
        
        html_content += """            </tbody>
        </table>
    </div>

    <div style="margin-top: 30px; padding: 20px; background-color: #e8f5e8; border-radius: 5px; color: #666; font-size: 12px;">
        <p>💡 每日报告说明：</p>
        <ul>
            <li>本报告只包含过去24小时内新发现的唯一Ref参数，无任何遗漏</li>
            <li>数据时间范围：过去24小时滚动窗口</li>
            <li>每个Ref参数显示首次发现的记录信息</li>
            <li>点击"链接"可直接访问目标网站</li>
            <li>此邮件由Google广告监控系统每日18:00自动生成</li>
        </ul>
    </div>

</body>
</html>
"""
        
        return html_content
    
    def _create_empty_daily_report(self, report_date):
        """创建空的每日报告"""
        current_time = datetime.now()
        twenty_four_hours_ago = current_time - timedelta(hours=24)
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .empty {{ text-align: center; padding: 40px; color: #666; }}
        .daily-badge {{ background-color: #6c757d; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📅 每日Google广告监控报告</h1>
        <p>报告日期: <strong>{report_date}</strong></p>
        <p>报告生成时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><span class="daily-badge">过去24小时新发现</span></p>
    </div>
    
    <div class="empty">
        <h2>📭 过去24小时无新发现</h2>
        <p>过去24小时内({twenty_four_hours_ago.strftime('%Y-%m-%d %H:%M')} ~ {current_time.strftime('%Y-%m-%d %H:%M')})未发现包含Ref参数的新广告数据</p>
        <p>监控系统正常运行中，将继续监控...</p>
    </div>
</body>
</html>
"""
    
    def _create_empty_report(self):
        """创建空报告"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .empty {{ text-align: center; padding: 40px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Google广告监控报告</h1>
        <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="empty">
        <h2>📭 暂无数据</h2>
        <p>最近8天内未发现包含Ref参数的广告数据</p>
    </div>
</body>
</html>
"""
    
    def _get_country_name(self, code):
        """获取国家中文名称"""
        country_map = {
            'in': '印度',
            'de': '德国', 
            'tw': '中国台湾',
            'ru': '俄罗斯',
            'es': '西班牙'
        }
        return country_map.get(code, code)
    
    def send_email(self, subject=None, recipients=None):
        """发送邮件"""
        try:
            print("📊 正在获取广告数据...")
            # 获取数据
            ads_data = self.get_recent_ads_data()
            print(f"   找到 {len(ads_data)} 个唯一Ref参数")
            
            print("📝 正在生成邮件内容...")
            # 生成邮件内容
            html_content = self.format_email_content(ads_data)
            
            # 设置邮件参数
            if not subject:
                ref_count = len(ads_data)
                subject = f"Google广告监控报告 - 发现{ref_count}个唯一Ref参数 ({datetime.now().strftime('%Y-%m-%d')})"
            
            if not recipients:
                recipients = self.email_config.get('daily_recipients', self.email_config['recipients'])
            
            print(f"📧 正在准备发送邮件...")
            print(f"   SMTP服务器: {self.email_config['smtp_server']}:{self.email_config['smtp_port']}")
            print(f"   发件人: {self.email_config['sender']}")
            print(f"   收件人: {', '.join(recipients)}")
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr(('Google广告监控系统', self.email_config['sender']))
            msg['To'] = ', '.join(recipients)
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            print("📤 正在发送邮件...")
            success_count = 0
            failed_recipients = []
            
            # 为每个收件人建立单独的SMTP连接（避免QQ邮箱多收件人问题）
            for i, recipient in enumerate(recipients, 1):
                print(f"   发送给 {recipient} ({i}/{len(recipients)})")
                server = None
                try:
                    # 为每个收件人创建新的连接
                    server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                    server.set_debuglevel(0)
                    server.starttls()
                    server.login(self.email_config['username'], self.email_config['password'])
                    
                    # 为单个收件人创建邮件副本
                    single_msg = MIMEMultipart('alternative')
                    single_msg['Subject'] = subject
                    single_msg['From'] = formataddr(('Google广告监控系统', self.email_config['sender']))
                    single_msg['To'] = recipient  # 单个收件人
                    single_msg.attach(html_part)
                    
                    # 发送邮件
                    result = server.send_message(single_msg, to_addrs=[recipient])
                    
                    # 检查发送结果
                    if isinstance(result, dict) and len(result) == 0:
                        success_count += 1
                        print(f"     ✅ 发送成功")
                    else:
                        failed_recipients.append(recipient)
                        print(f"     ⚠️ 发送可能失败，结果: {result}")
                        
                except smtplib.SMTPRecipientsRefused as e:
                    failed_recipients.append(recipient)
                    print(f"     ❌ 收件人被拒绝: {str(e)}")
                except smtplib.SMTPDataError as e:
                    failed_recipients.append(recipient)
                    print(f"     ❌ 数据错误: {str(e)}")
                except Exception as e:
                    failed_recipients.append(recipient)
                    print(f"     ❌ 发送失败: {str(e)}")
                finally:
                    # 关闭当前连接
                    if server:
                        try:
                            server.quit()
                        except smtplib.SMTPResponseException as e:
                            # 忽略QQ邮箱QUIT异常
                            if e.smtp_code != -1:
                                print(f"     ⚠️ QUIT异常: {str(e)}")
                        except Exception:
                            pass
                        finally:
                            try:
                                server.close()
                            except:
                                pass
                
            if success_count > 0:
                print(f"✅ 邮件发送完成 ({success_count}/{len(recipients)} 成功)")
                print(f"   成功收件人数: {success_count}")
                print(f"   Ref参数数量: {len(ads_data)}")
                if failed_recipients:
                    print(f"   ⚠️ 发送失败的收件人: {', '.join(failed_recipients)}")
                return True
            else:
                print("❌ 所有收件人发送失败")
                return False
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_test_email(self):
        """发送测试邮件"""
        test_recipients = self.email_config['recipients']  # 使用测试收件人列表
        subject = f"[测试] Google广告监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        return self.send_email(subject=subject, recipients=test_recipients)
    
    def send_daily_email(self):
        """发送每日邮件 - 只包含过去24小时新发现的ref参数"""
        daily_recipients = self.email_config['daily_recipients']
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            print("📊 正在获取过去24小时广告数据...")
            # 获取过去24小时数据
            ads_data = self.get_today_ads_data()
            ref_count = len(ads_data)
            print(f"   过去24小时发现 {ref_count} 个唯一Ref参数")
            
            # 构建每日报告的邮件主题
            subject = f"[每日报告] Google广告监控 - 过去24小时发现{ref_count}个新Ref参数 ({current_date})"
            
            # 生成当日报告的邮件内容
            print("📝 正在生成每日邮件内容...")
            html_content = self.format_daily_email_content(ads_data, current_date)
            
            print(f"📧 正在准备发送每日邮件...")
            print(f"   收件人: {', '.join(daily_recipients)}")
            
            # 创建邮件
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.utils import formataddr
            import smtplib
            
            success_count = 0
            failed_recipients = []
            
            # 为每个收件人建立单独的SMTP连接
            for i, recipient in enumerate(daily_recipients, 1):
                print(f"   发送给 {recipient} ({i}/{len(daily_recipients)})")
                server = None
                try:
                    # 创建邮件
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = subject
                    msg['From'] = formataddr(('Google广告监控系统', self.email_config['sender']))
                    msg['To'] = recipient
                    
                    # 添加HTML内容
                    html_part = MIMEText(html_content, 'html', 'utf-8')
                    msg.attach(html_part)
                    
                    # 创建SMTP连接
                    server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                    server.set_debuglevel(0)
                    server.starttls()
                    server.login(self.email_config['username'], self.email_config['password'])
                    
                    # 发送邮件
                    result = server.send_message(msg, to_addrs=[recipient])
                    
                    if isinstance(result, dict) and len(result) == 0:
                        success_count += 1
                        print(f"     ✅ 发送成功")
                    else:
                        failed_recipients.append(recipient)
                        print(f"     ⚠️ 发送可能失败，结果: {result}")
                        
                except Exception as e:
                    failed_recipients.append(recipient)
                    print(f"     ❌ 发送失败: {str(e)}")
                finally:
                    if server:
                        try:
                            server.quit()
                        except:
                            pass
                        finally:
                            try:
                                server.close()
                            except:
                                pass
            
            if success_count > 0:
                print(f"✅ 每日邮件发送完成 ({success_count}/{len(daily_recipients)} 成功)")
                print(f"   过去24小时发现Ref参数数量: {ref_count}")
                if failed_recipients:
                    print(f"   ⚠️ 发送失败的收件人: {', '.join(failed_recipients)}")
                return True
            else:
                print("❌ 所有收件人发送失败")
                return False
                
        except Exception as e:
            print(f"❌ 每日邮件发送失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_weekly_email(self):
        """发送每周邮件"""
        weekly_recipients = self.email_config['weekly_recipients']
        week_number = datetime.now().isocalendar()[1]
        subject = f"[周报] Google广告监控汇总 - 第{week_number}周 ({datetime.now().strftime('%Y-%m-%d')})"
        
        return self.send_email(subject=subject, recipients=weekly_recipients)


def main():
    """命令行入口"""
    import sys
    
    sender = EmailSender()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("🧪 发送测试邮件...")
        success = sender.send_test_email()
    else:
        print("📧 发送每日报告邮件...")
        success = sender.send_email()
    
    if success:
        print("🎉 邮件发送完成!")
    else:
        print("💥 邮件发送失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()