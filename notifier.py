from dotenv import load_dotenv
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote_plus

# ── 加载 .env ─────────────────────────────────────────
# 自动寻找与本文件同目录下的 .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── 配置 ───────────────────────────────────────────────
BARK_KEY = os.getenv("BARK_KEY")
if not BARK_KEY:
    print("[Notifier] 警告：环境变量 BARK_KEY 未设置，将跳过 BARK 推送。")

# 这里自动定位到本模块同目录下的 docs/weather.xml
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RSS_FILE = os.getenv("RSS_FILE", os.path.join(BASE_DIR, "docs", "weather.xml"))

FEED_TITLE = "天气通知"
FEED_LINK  = "https://<你的用户名>.github.io/weather-rss/weather.xml"
FEED_DESC  = "通过 RSS 订阅的天气更新"

# ── 功能函数 ───────────────────────────────────────────

def send_bark(title: str, body: str):
    """通过 BARK 推送一次通知。"""
    if not BARK_KEY:
        return
    url = f"https://api.day.app/{BARK_KEY}/{quote_plus(title)}/{quote_plus(body)}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        print("[Notifier] BARK 推送成功")
    except Exception as e:
        print(f"[Notifier] BARK 推送失败：{e}")

def update_rss(item_title: str, item_description: str):
    """写入或更新 RSS 文件，并为每次更新生成唯一 GUID。"""
    # 1. 构造 RSS 树
    rss     = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text         = FEED_TITLE
    ET.SubElement(channel, 'link').text          = FEED_LINK
    ET.SubElement(channel, 'description').text   = FEED_DESC
    ET.SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    ET.SubElement(channel, 'language').text      = 'zh-cn'

    item = ET.SubElement(channel, 'item')
    ET.SubElement(item, 'title').text       = item_title
    ET.SubElement(item, 'description').text = item_description

    # 使用当前 UTC 时间生成 pubDate 和唯一 GUID
    now = datetime.utcnow()
    pub_date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
    ET.SubElement(item, 'pubDate').text = pub_date

    # 生成不重复的 GUID，并标记为非永久链接
    guid = ET.SubElement(item, 'guid', isPermaLink='false')
    guid.text = now.strftime('weather-%Y%m%d%H%M%S')

    tree = ET.ElementTree(rss)

    # 2. 确保 docs/ 目录存在
    os.makedirs(os.path.dirname(RSS_FILE), exist_ok=True)

    # 3. 写入 RSS 文件
    tree.write(RSS_FILE, encoding='utf-8', xml_declaration=True)
    print(f"[Notifier] 已更新 RSS：{RSS_FILE}")