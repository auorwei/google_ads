#!/usr/bin/env python3
"""
数据库路径验证脚本
确保所有组件都指向项目内的正确数据库文件
"""

import os
import sys
from database import AdDatabase
from email_sender import EmailSender
from config import DATABASE_NAME

def test_database_paths():
    """测试所有数据库路径"""
    print("🔍 数据库路径验证测试")
    print("=" * 50)
    
    # 显示当前工作目录
    print(f"当前工作目录: {os.getcwd()}")
    
    # 显示项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"项目根目录: {project_root}")
    
    # 测试 config.py 中的配置
    print(f"\nconfig.DATABASE_NAME: {DATABASE_NAME}")
    print(f"是否为绝对路径: {os.path.isabs(DATABASE_NAME)}")
    
    # 测试 AdDatabase 类
    print(f"\n📊 测试 AdDatabase 类...")
    try:
        db = AdDatabase()
        print(f"✅ AdDatabase 路径: {db.db_path}")
        print(f"   数据库文件存在: {os.path.exists(db.db_path)}")
        
        # 测试数据库连接
        stats = db.get_scrape_stats()
        print(f"   数据库可访问: ✅")
        print(f"   总广告数: {stats['total_ads']}")
    except Exception as e:
        print(f"❌ AdDatabase 错误: {e}")
    
    # 测试 EmailSender 类
    print(f"\n📧 测试 EmailSender 类...")
    try:
        sender = EmailSender()
        # 测试获取数据
        recent_data = sender.get_recent_ads_data(days=1)
        print(f"✅ EmailSender 数据库访问正常")
        print(f"   最近1天数据条数: {len(recent_data)}")
    except Exception as e:
        print(f"❌ EmailSender 错误: {e}")
    
    # 验证所有路径都指向同一个数据库
    print(f"\n🎯 路径一致性验证...")
    paths = []
    
    # AdDatabase 路径
    try:
        db = AdDatabase()
        paths.append(("AdDatabase", db.db_path))
    except Exception as e:
        paths.append(("AdDatabase", f"错误: {e}"))
    
    # 手动计算的邮件发送器路径
    if os.path.isabs(DATABASE_NAME):
        email_db_path = DATABASE_NAME
    else:
        email_project_root = os.path.dirname(os.path.abspath(__file__))
        email_db_path = os.path.join(email_project_root, DATABASE_NAME)
    paths.append(("EmailSender计算路径", email_db_path))
    
    # 显示所有路径
    all_same = True
    first_path = None
    for component, path in paths:
        print(f"   {component}: {path}")
        if first_path is None:
            first_path = path
        elif path != first_path:
            all_same = False
    
    if all_same:
        print(f"\n✅ 所有组件都指向同一个数据库文件!")
        print(f"   统一路径: {first_path}")
        
        # 验证这是项目内的数据库
        if project_root in first_path:
            print(f"✅ 确认数据库位于项目内部!")
        else:
            print(f"⚠️ 警告: 数据库不在项目目录内")
    else:
        print(f"❌ 不同组件指向了不同的数据库文件!")

def simulate_cron_environment():
    """模拟cron环境测试"""
    print(f"\n🕐 模拟 Cron 环境测试")
    print("=" * 50)
    
    # 保存原始工作目录
    original_cwd = os.getcwd()
    
    # 切换到不同目录模拟cron环境
    test_dirs = ['/tmp', '/Users/w', '/']
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            try:
                os.chdir(test_dir)
                print(f"\n📍 切换到目录: {test_dir}")
                
                # 测试数据库路径
                db = AdDatabase()
                print(f"   数据库路径: {db.db_path}")
                
                # 验证是否为项目内路径
                if '/Users/w/Documents/code/google_ads/google_ads.db' in db.db_path:
                    print(f"   ✅ 正确指向项目内数据库")
                else:
                    print(f"   ❌ 指向了错误的数据库位置")
                    
            except Exception as e:
                print(f"   ❌ 错误: {e}")
    
    # 恢复原始工作目录
    os.chdir(original_cwd)

if __name__ == "__main__":
    test_database_paths()
    simulate_cron_environment()
    print(f"\n🎉 验证完成!")