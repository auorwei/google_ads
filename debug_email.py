#!/usr/bin/env python3
"""
邮件发送调试工具
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from config import EMAIL_CONFIG


def test_single_recipient(recipient):
    """测试发送给单个收件人"""
    print(f"\n🧪 测试发送给: {recipient}")
    
    try:
        # 创建简单的测试邮件
        msg = MIMEMultipart()
        msg['Subject'] = f"测试邮件 - {recipient}"
        msg['From'] = formataddr(('测试系统', EMAIL_CONFIG['sender']))
        msg['To'] = recipient
        
        # 添加简单文本内容
        text_content = f"""
这是一封发送给 {recipient} 的测试邮件。
发送时间: {__import__('datetime').datetime.now()}
"""
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        
        # 发送邮件
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.set_debuglevel(1)  # 启用详细调试
            print("连接SMTP服务器...")
            server.starttls()
            print("启用TLS...")
            server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
            print("登录成功...")
            
            print("开始发送...")
            result = server.send_message(msg)
            print(f"发送结果: {result}")
            
        print("✅ 发送成功")
        return True
        
    except Exception as e:
        print(f"❌ 发送失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_send():
    """测试批量发送"""
    print("\n🔄 测试批量发送...")
    recipients = EMAIL_CONFIG['daily_recipients']
    
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "批量测试邮件"
        msg['From'] = formataddr(('测试系统', EMAIL_CONFIG['sender']))
        msg['To'] = ', '.join(recipients)  # 设置所有收件人
        
        text_content = f"""
这是一封批量测试邮件。
收件人: {', '.join(recipients)}
发送时间: {__import__('datetime').datetime.now()}
"""
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.set_debuglevel(1)
            server.starttls()
            server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
            
            # 尝试一次性发送给所有收件人
            print("尝试一次性发送给所有收件人...")
            result = server.sendmail(EMAIL_CONFIG['sender'], recipients, msg.as_string())
            print(f"发送结果: {result}")
            
        print("✅ 批量发送成功")
        return True
        
    except Exception as e:
        print(f"❌ 批量发送失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_smtp_connection():
    """测试SMTP连接"""
    print("\n🔍 测试SMTP连接...")
    
    try:
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.set_debuglevel(1)
        
        print("启用TLS...")
        server.starttls()
        
        print("测试登录...")
        server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
        
        print("获取服务器功能...")
        print(f"服务器功能: {server.esmtp_features}")
        
        print("测试EHLO...")
        code, response = server.ehlo()
        print(f"EHLO响应: {code} - {response}")
        
        server.quit()
        print("✅ SMTP连接测试成功")
        return True
        
    except Exception as e:
        print(f"❌ SMTP连接测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🔧 开始邮件发送调试...")
    print(f"SMTP配置: {EMAIL_CONFIG['smtp_server']}:{EMAIL_CONFIG['smtp_port']}")
    print(f"发件人: {EMAIL_CONFIG['sender']}")
    print(f"测试收件人: {EMAIL_CONFIG['daily_recipients']}")
    
    # 1. 测试SMTP连接
    test_smtp_connection()
    
    # 2. 测试发送给每个收件人
    for recipient in EMAIL_CONFIG['daily_recipients']:
        test_single_recipient(recipient)
    
    # 3. 测试批量发送
    test_batch_send()


if __name__ == "__main__":
    main()