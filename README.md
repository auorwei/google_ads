# Google SERP 广告数据抓取工具

使用 Bright Data API 获取 Google 搜索结果页面，提取广告信息并存储到 SQLite 数据库中。

## 功能特点

- ✅ 使用 Bright Data API 获取 Google SERP 数据
- ✅ 智能识别和提取广告信息（标题、URL、描述等）
- ✅ 支持多关键词、多国家批量抓取
- ✅ SQLite 数据库存储，支持去重
- ✅ 原始 HTML 文件存档，便于回溯分析
- ✅ 详细的抓取日志和统计信息
- ✅ 数据导出功能

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

在 `config.py` 文件中配置你的 API 信息：

```python
API_KEY = 'your_bright_data_api_key'
ZONE = 'your_zone_name'
```

## 使用方法

### 1. 批量抓取（默认模式）

抓取配置文件中所有关键词和国家的组合：

```bash
python main.py
```

或明确指定批量模式：

```bash
python main.py --mode batch
```

### 2. 单次抓取

抓取特定关键词在特定国家的数据：

```bash
python main.py --mode single --keyword "bingx" --country "us"
```

### 3. 显示统计信息

查看抓取统计和数据库状态：

```bash
python main.py --mode stats
```

### 4. 查看配置

显示当前配置的关键词和国家列表：

```bash
python main.py --list-config
```

### 5. 导出数据

将数据库中的广告数据导出为 CSV 文件：

```bash
python main.py --export ads_data.csv
```

## 文件结构

```
google_ads/
├── main.py              # 主程序入口
├── scraper.py           # 核心抓取逻辑
├── ad_extractor.py      # 广告数据提取模块
├── database.py          # 数据库操作模块
├── config.py            # 配置文件
├── requirements.txt     # Python依赖
├── google_ads.db        # SQLite数据库（运行后生成）
├── htmls/              # HTML文件存储目录
└── README.md           # 说明文档
```

## 数据库结构

### ads_data 表
存储提取的广告数据：
- `keyword`: 搜索关键词
- `country_code`: 国家代码  
- `ad_url`: 广告URL
- `target_url`: 广告跳转目标URL
- `ad_title`: 广告标题
- `ad_description`: 广告描述
- `position`: 广告位置
- `scrape_time`: 抓取时间
- `html_file_path`: 对应的HTML文件路径

### scrape_logs 表  
记录抓取日志：
- `keyword`: 关键词
- `country_code`: 国家代码
- `status`: 抓取状态 (success/failed)
- `ads_found`: 发现的广告数量
- `error_message`: 错误信息
- `scrape_time`: 抓取时间

## 注意事项

1. **API限制**: 请合理控制抓取频率，避免触发API限制
2. **存储空间**: HTML文件会占用较多存储空间，建议定期清理
3. **网络稳定**: 确保网络连接稳定，程序有重试机制但不能解决所有网络问题
4. **合规使用**: 请确保使用符合相关法律法规和网站服务条款

## 故障排除

### 常见问题

1. **API请求失败**
   - 检查API密钥和区域配置是否正确
   - 确认账户余额充足
   - 检查网络连接

2. **没有发现广告**
   - 某些关键词可能确实没有广告
   - Google的页面结构可能发生变化，需要更新广告识别规则

3. **数据库错误**
   - 确保有写入权限
   - 检查磁盘空间

## 开发扩展

如需扩展功能，主要修改以下文件：

- `ad_extractor.py`: 修改广告识别规则
- `config.py`: 添加新的配置选项  
- `database.py`: 扩展数据库结构
- `scraper.py`: 修改抓取逻辑