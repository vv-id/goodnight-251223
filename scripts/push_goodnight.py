import os
import sys
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =============================
# 0) 只在本地指定小时推送（默认：San Diego 10:00）
# =============================
TZ_LOCAL = os.environ.get("LOCAL_TZ", "America/Los_Angeles")
PUSH_HOUR_LOCAL = int(os.environ.get("PUSH_HOUR_LOCAL", "10"))

now_local = datetime.now(ZoneInfo(TZ_LOCAL))
if now_local.hour != PUSH_HOUR_LOCAL:
    print(f"[SKIP] Local time is {now_local:%Y-%m-%d %H:%M:%S %Z}, not {PUSH_HOUR_LOCAL}:00")
    sys.exit(0)

# =============================
# 1) 环境变量
# =============================
SENDKEY = os.environ.get("SERVERCHAN_SENDKEY")  # Secret
CITY = os.environ.get("CITY", "San Diego")
LAT = os.environ.get("LAT")
LON = os.environ.get("LON")

if not SENDKEY:
    raise SystemExit("Missing SERVERCHAN_SENDKEY (Repository secret)")
if not (LAT and LON):
    raise SystemExit("Missing LAT/LON (Repository variables)")

MOOD = os.environ.get("MOOD", "😄 微笑")
EXERCISE_TIP = os.environ.get("EXERCISE_TIP", "多运动，注意拉伸噢～")

# =============================
# 2) Open-Meteo：当前天气（无需 key）
# =============================
def weather_code_to_text(code: int) -> str:
    mapping = {
        0: "晴朗",
        1: "大部晴朗",
        2: "局部多云",
        3: "阴",
        45: "雾",
        48: "冻雾",
        51: "毛毛雨（轻）",
        53: "毛毛雨（中）",
        55: "毛毛雨（强）",
        56: "冻毛毛雨（轻）",
        57: "冻毛毛雨（强）",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "冻雨（轻）",
        67: "冻雨（强）",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "阵雨（轻）",
        81: "阵雨（中）",
        82: "阵雨（强）",
        85: "阵雪（轻）",
        86: "阵雪（强）",
        95: "雷暴",
        96: "雷暴（伴小冰雹）",
        99: "雷暴（伴大冰雹）",
    }
    return mapping.get(code, f"未知天气（code={code}）")

def fetch_weather(lat: str, lon: str, tz_name: str):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,weather_code",
        "timezone": tz_name,
        "temperature_unit": "celsius",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    cur = data.get("current", {})
    temp = cur.get("temperature_2m")
    feels = cur.get("apparent_temperature")
    wcode = cur.get("weather_code")

    if temp is None or feels is None or wcode is None:
        raise RuntimeError(f"Weather data missing fields: {cur}")

    wtext = weather_code_to_text(int(wcode))
    return float(temp), float(feels), wtext

temp, feels, wtext = fetch_weather(LAT, LON, TZ_LOCAL)

# =============================
# 3) 组装推送内容（Server酱 Markdown）
# =============================
title = f"{CITY} 今日提醒 ☀️"

desp = "\n".join([
    f"**当地天气（{CITY}）**",
    f"- 气温：**{temp:.1f}°C**",
    f"- 体感：**{feels:.1f}°C**",
    f"- 天气：**{wtext}**",
    "",
    "**心情**",
    f"- {MOOD}",
    "",
    "**运动提示**",
    f"- {EXERCISE_TIP}",
    "",
    f"_推送时间：{now_local:%Y-%m-%d %H:%M %Z}_",
])

# =============================
# 4) 调 Server酱推送
# =============================
push_url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
payload = {"title": title, "desp": desp}

resp = requests.post(push_url, data=payload, timeout=20)
resp.raise_for_status()

j = resp.json()
print("[ServerChan Response]", j)
print("[OK] Push sent.")
