# weather-rss
Weather RSS 天气通知

使用 GitHub Pages + RSS + BARK + Slack 实时推送台北/新北天气预报与降雨乡镇信息。

⸻

:page_facing_up: 项目简介

本项目通过台湾中央气象署开放资料 API，自动获取：
	1.	台北市 & 新北市当日 24 小时天气预报（6 小时分段）；
	2.	全台可能降雨的乡镇列表；
	3.	台风警报与热带气旋状态；

并将结果以 RSS 格式生成到 docs/weather.xml，通过 GitHub Pages 发布；
同时使用 BARK 推送手机通知，并可选用 Slack RSS 机器人订阅频道消息。
⸻
