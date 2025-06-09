# 🌤️  Taiwan Weather RSS

> 自动抓取中央气象署开放资料。生成 RSS 给 GitHub Pages 发布，并支持 Bark 推送至手机。

## 目录结构

```
weather-rss/
├— main.py                    # 入口：生成今日天气 RSS
├— services/
│   └— weather_service.py     # 接口解析，已统一 Asia/Taipei 时区
├— notifier.py                # 写 RSS 和 Bark 推送
├— docs/weather.xml           # 被 GitHub Pages 发布的 RSS
├— .github/workflows/
│   └— weather.yml            # GitHub Actions 定时任务
├— requirements.txt           # 依赖列表
└— .gitignore                 # 忽略 .env / __pycache__ / *.pyc
```

## 快速开始

### 1. GitHub Secrets 配置

| Secret Key    | 用途                                                               |
| ------------- | ---------------------------------------------------------------- |
| `CWA_API_KEY` | 中央气象署 OpenData 授权码 (必填)                                          |
| `BARK_KEY`    | Bark 推送的 device key (可选)                                         |
| `RSS_LINK`    | RSS URL，如 `https://<username>.github.io/weather-rss/weather.xml` |

> `RSS_LINK` 作为 RSS `<link>` 内容，便于转换 GitHub Pages 路径

### 2. GitHub Actions 定时解析


## 功能概览

| 功能        | 说明                                    |
| --------- | ------------------------------------- |
| 县市 36h 预报 | 00-06 / 06-18 / 18-06 每6小时段天气，含降雨率和温度 |
| 全台降雨乡镇    | 为 PoP > 0% 的乡镇列表                      |
| 台风警报      | 含 "頝风" 关键词的特报项                        |
| 热带气旋      |             
| 七日预报      | 台北/新北 简单月/日+天气+温度预报                   |
| RSS 输出    | 写入 docs/weather.xml                   |
| Bark 推送   | 选填，推送同步内容                             |


## 时区处理

* GitHub Actions 为 **UTC 时区**，输出 RSS 时间使用 `datetime.utcnow()`
* 与 API 相关时间系，都统一使用 `Asia/Taipei` 解析和转换


> 有任何问题或优化建议欢迎 Issue / PR
