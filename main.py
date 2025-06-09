from services.weather_service import get_weather_summary
import notifier

def main():
    # 天气
    w_title, w_summary = get_weather_summary()
    notifier.update_rss(w_title, w_summary)
    notifier.send_bark(w_title, w_summary)


if __name__=="__main__":
    main()