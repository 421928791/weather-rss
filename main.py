from services.weather_service import get_weather_summary
import notifier

def main():
    title, summary = get_weather_summary()
    notifier.update_rss(title, summary)
    notifier.send_bark(title, summary)

if __name__ == "__main__":
    main()