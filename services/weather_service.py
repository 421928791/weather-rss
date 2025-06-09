import os
import requests
from dateutil import parser
from datetime import datetime, timedelta 
from zoneinfo import ZoneInfo
TPE = ZoneInfo("Asia/Taipei")

CWA_API_KEY = os.getenv("CWA_API_KEY")
if not CWA_API_KEY:
    raise RuntimeError("环境变量 CWA_API_KEY 未设置，请先 export CWA_API_KEY=你的API_KEY")

ENDPOINTS = {
    "county_36h":    "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001",
    "township_3h":   "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091",
    "alerts":        "https://opendata.cwa.gov.tw/api/v1/rest/datastore/W-C0033-001",
    "typhoon_track": "https://opendata.cwa.gov.tw/api/v1/rest/datastore/W-C0034-005",
}
# 县市级 7 天预报
ENDPOINT_7DAY = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-003"
# 台北市乡镇未来 1 周预报
ENDPOINT_TPE_TOWN_WEEK = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-063"
# 新北市乡镇未来 1 周预报
ENDPOINT_NTP_TOWN_WEEK = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-071"
# 天气特报详情
ENDPOINT_ALERTS_DETAIL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/W-C0033-002"


def fetch_city_36h(city_name: str) -> dict:
    """抓取县市 36 小时天气预报，返回第一个匹配的 location 数据。"""
    params = {"Authorization": CWA_API_KEY, "locationName": city_name}
    r = requests.get(ENDPOINTS["county_36h"], params=params, timeout=10)
    r.raise_for_status()
    return r.json()["records"]["location"][0]


def get_today_segments(city_name: str, data: dict) -> list[str]:
    """提取今天 00:00–24:00 内每个 6 小时段的天气摘要。"""
    elems = {e["elementName"]: e for e in data.get("weatherElement", [])}
    wx = elems.get("Wx", {})
    pop = elems.get("PoP", {})
    mint = elems.get("MinT", {})
    maxt = elems.get("MaxT", {})
    today = datetime.now(TPE).date()
    segments = []

    for i, seg in enumerate(wx.get("time", [])):
        st = parser.isoparse(seg["startTime"]).astimezone(TPE)
        if st.date() != today:
            continue
        ed = parser.isoparse(seg["endTime"]).astimezone(TPE) 
        desc = seg.get("parameter", {}).get("parameterName", "")
        rain = pop.get("time", [{}])[i].get("parameter", {}).get("parameterName", "")
        tmin = mint.get("time", [{}])[i].get("parameter", {}).get("parameterName", "")
        tmax = maxt.get("time", [{}])[i].get("parameter", {}).get("parameterName", "")
        segments.append(
            f"{city_name} {st:%H:%M}–{ed:%H:%M}: "
            f"{desc}，降雨 {rain}% ，气温 {tmin}～{tmax}°C"
        )
    return segments


def fetch_rainy_townships() -> list[str]:
    """抓取全台可能降雨乡镇列表（3 小时区间机率>0）。"""
    r = requests.get(ENDPOINTS["township_3h"], params={"Authorization": CWA_API_KEY}, timeout=10)
    r.raise_for_status()
    groups = r.json().get("records", {}).get("locations", [])
    rainy = []

    for grp in groups:
        county = grp.get("locationsName", "")
        for loc in grp.get("location", []):
            pop_elem = next(
                (e for e in loc.get("weatherElement", []) if e.get("elementName") in ("PoP", "ProbabilityOfPrecipitation")),
                None
            )
            if not pop_elem:
                continue
            for t in pop_elem.get("time", []):
                val = int(t.get("elementValue", [{}])[0].get("value", 0))
                if val > 0:
                    rainy.append(f"{county}{loc.get('locationName','')}")
                    break
    return rainy


def fetch_typhoon_alerts() -> list[str]:
    """抓取含“颱風”关键字的天气警特报列表。"""
    r = requests.get(ENDPOINTS["alerts"], params={"Authorization": CWA_API_KEY}, timeout=10)
    r.raise_for_status()
    recs = r.json().get("records", {})
    locs = recs.get("locations", [{}])[0].get("location", []) if isinstance(recs, dict) else recs
    alerts = []

    for loc in locs:
        for elem in loc.get("weatherElement", []):
            for t in elem.get("time", []):
                desc = t.get("parameter", {}).get("parameterName", "")
                if "颱風" in desc:
                    alerts.append(f"{loc.get('locationName','')}：{desc}")
    return alerts


def fetch_typhoon_tracks() -> list[dict]:
    """抓取当前活跃热带气旋（台风）列表。"""
    r = requests.get(ENDPOINTS["typhoon_track"], params={"Authorization": CWA_API_KEY}, timeout=10)
    r.raise_for_status()
    recs = r.json().get("records", {})
    return recs if isinstance(recs, list) else recs.get("typhoon") or recs.get("typhoons") or []


def get_weather_summary() -> tuple[str, str]:
    """生成今日天气摘要（36 小时县市级预报 + 乡镇、台风等）。"""
    summary_parts = []
    for city in ["臺北市", "新北市"]:
        try:
            data = fetch_city_36h(city)
            segs = get_today_segments(city, data)
            summary_parts.append(f"── {city} 今日预报 ──")
            summary_parts.extend(segs)
        except Exception as e:
            summary_parts.append(f"[Error] 获取{city}今日预报失败：{e}")
    # 降雨乡镇
    rainy = fetch_rainy_townships()
    summary_parts.append("── 全台可能降雨乡镇 ──")
    summary_parts.append("、".join(rainy) if rainy else "无可能降雨乡镇")
    # 台风警报
    alerts = fetch_typhoon_alerts()
    summary_parts.append("── 台风相关警报 ──")
    summary_parts.append("\n".join(alerts) if alerts else "无台风警报")
    # 热带气旋
    tracks = fetch_typhoon_tracks()
    summary_parts.append("── 当前热带气旋 ──")
    if tracks:
        for ty in tracks:
            summary_parts.append(f"编号 {ty.get('typhoonNo','N/A')}：{ty.get('typhoonNameZh','')} / {ty.get('typhoonNameEn','')}")
    else:
        summary_parts.append("无活跃热带气旋")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = f"今日天气更新 ({now_str})"
    summary = "\n".join(summary_parts)
    return title, summary


def get_weekly_summary() -> tuple[str, str]:
    """生成未来 7 天的县市级天气摘要。"""
    summary_parts = []
    for city in ["臺北市", "新北市"]:
        try:
            params = {"Authorization": CWA_API_KEY, "locationName": city}
            r = requests.get(ENDPOINT_7DAY, params=params, timeout=10)
            r.raise_for_status()
            recs = r.json().get("records", {})
            loc = recs.get("location", [])[0] if isinstance(recs.get("location", []), list) else recs.get("location")
            summary_parts.append(f"── {city} 七日县市级预报 ──")
            elems = {e.get("elementName"): e for e in loc.get("weatherElement", [])}
            wx_times = elems.get("Wx", {}).get("time", [])
            min_times = elems.get("MinT", {}).get("time", [])
            max_times = elems.get("MaxT", {}).get("time", [])
            for i in range(len(wx_times)):
                date = (
                    (parser.isoparse(wx_times[i]["startTime"]) + timedelta(hours=0))
                    .astimezone() 
                    .strftime("%m/%d")
                )
                desc = wx_times[i].get("parameter", {}).get("parameterName", "")
                tmin = min_times[i].get("parameter", {}).get("parameterName", "")
                tmax = max_times[i].get("parameter", {}).get("parameterName", "")
                summary_parts.append(f"{date}: {desc}，{tmin}～{tmax}°C")
        except Exception as e:
            summary_parts.append(f"[Error] 获取{city}七日县市级预报失败：{e}")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = f"七日天气预报 ({now_str})"
    summary = "\n".join(summary_parts)
    return title, summary


def fetch_township_weekly(endpoint: str, city_towns: list[str]) -> dict[str, str]:
    """调用乡镇未来 1 周预报接口，返回 {locationName: description}。"""
    params = {
        "Authorization": CWA_API_KEY,
        "LocationName": city_towns,
        "ElementName": ["天氣預報綜合描述"],
        "format": "JSON",
        "limit": len(city_towns),
    }
    r = requests.get(endpoint, params=params, timeout=10)
    r.raise_for_status()
    recs = r.json().get("records", {}).get("locations", [])
    result = {}
    for grp in recs:
        for loc in grp.get("location", []):
            name = loc.get("locationName", "")
            descs = [t.get("parameter", {}).get("parameterName", "") for t in loc.get("weatherElement", [])[0].get("time", [])]
            result[name] = "；".join(descs)
    return result


def fetch_alerts_detail() -> list[str]:
    """调用天气特报详情接口，返回每条警特报的简要描述列表。"""
    params = {"Authorization": CWA_API_KEY, "format": "JSON"}
    r = requests.get(ENDPOINT_ALERTS_DETAIL, params=params, timeout=10)
    r.raise_for_status()
    recs = r.json().get("records", {}).get("locations", [])
    alerts = []
    for grp in recs:
        for info in grp.get("location", []):
            for elem in info.get("weatherElement", []):
                for t in elem.get("time", []):
                    desc = t.get("parameter", {}).get("parameterName") or t.get("parameterDescription", "")
                    area = info.get("locationName", "")
                    if desc:
                        alerts.append(f"{area}：{desc}")
    return alerts