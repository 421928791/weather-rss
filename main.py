from services.weather_service import get_weather_summary
import notifier
from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    title, summary = get_weather_summary()

    # 重写标题，加上台北时间
    tpe_now_str = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M")
    title = f"今日天气更新（台北时间 {tpe_now_str}）"

    notifier.update_rss(title, summary)
    notifier.send_bark(title, summary)

if __name__ == "__main__":
    main()