import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


# =============================
# 1) 只在 San Diego 10:00 发送（自动适配夏令时）
# =============================
now_sd = datetime.now(ZoneInfo("America/Los_Angeles"))
#if now_sd.hour != 10:
    #print("Not 10AM in San Diego, exit.")
    #raise SystemExit(0)


# =============================
# 2) 环境变量
# =============================
SENDKEY = os.environ.get("SERVERCHAN_SENDKEY")
CITY = os.environ.get("CITY", "San Diego")
LAT = os.environ.get("LAT")
LON = os.environ.get("LON")
API_BASE = os.environ.get("GOODNIGHT_API_BASE")
USER = os.environ.get("GOODNIGHT_USER", "her")

if not SENDKEY:
    raise SystemExit("Missing SERVERCHAN_SENDKEY")
if not (LAT and LON):
    raise SystemExit("Missing LAT/LON")
if not API_BASE:
    raise SystemExit("Missing GOODNIGHT_API_BASE")


# =============================
# 3) 天气：体感 + 今日高低 + emoji
# Open-Meteo：不需要 key
# =============================
weather_url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&current=temperature_2m,apparent_temperature,weather_code"
    "&daily=temperature_2m_max,temperature_2m_min"
    "&timezone=America/Los_Angeles"
)

w = requests.get(weather_url, timeout=10).json()

cur = w.get("current", {})
daily = w.get("daily", {})

temp = cur.get("temperature_2m")
feels = cur.get("apparent_temperature")
code = cur.get("weather_code")

tmax = (daily.get("temperature_2m_max") or [None])[0]
tmin = (daily.get("temperature_2m_min") or [None])[0]


def code_to_desc_and_emoji(c):
    # Open-Meteo WMO weather codes: https://open-meteo.com/en/docs
    if c is None:
        return "未知", "❓"
    if c == 0:
        return "晴", "☀️"
    if c in (1, 2):
        return "少云", "🌤️"
    if c == 3:
        return "多云", "☁️"
    if c in (45, 48):
        return "雾", "🌫️"
    if c in (51, 53, 55, 56, 57):
        return "毛毛雨", "🌦️"
    if c in (61, 63, 65, 66, 67):
        return "雨", "🌧️"
    if c in (71, 73, 75, 77, 85, 86):
        return "雪", "🌨️"
    if c in (80, 81, 82):
        return "阵雨", "🌦️"
    if c in (95, 96, 99):
        return "雷暴", "⛈️"
    return "未知", "❓"


weather_desc, emoji = code_to_desc_and_emoji(code)

# 为了通知好看，温度统一保留 0 或 1 位小数都行；这里四舍五入到整数
def fmt_num(x):
    return "N/A" if x is None else str(int(round(float(x))))

temp_s = fmt_num(temp)
feels_s = fmt_num(feels)
tmax_s = fmt_num(tmax)
tmin_s = fmt_num(tmin)


# =============================
# 4) 获取状态：只用心情 + 睡眠（不出现人称）
# =============================
state_url = f"{API_BASE}/state?user={USER}"
state = requests.get(state_url, timeout=10).json()

mood_text = (state.get("mood") or {}).get("text", "未记录")

sleep_hours = (state.get("sleep") or {}).get("hours")
sleep_line = f"{sleep_hours}h" if sleep_hours else "未同步"


# =============================
# 5) 推送：通知栏尽量直出（用 title，多行）
# =============================
title = (
    f"{CITY} {emoji}\n\n"
    f"🙂 {mood_text}\n"
    f"{emoji} {temp_s}° 体感{feels_s}°  ↑{tmax_s}° ↓{tmin_s}°\n"
    f"🛌 {sleep_line}"
)

api = f"https://sctapi.ftqq.com/{SENDKEY}.send"
r = requests.post(api, data={"title": title}, timeout=10)
print(r.text)

