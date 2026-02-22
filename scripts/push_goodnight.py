import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =============================
# 1. 只在 San Diego 10:00 发送
# =============================
now_sd = datetime.now(ZoneInfo("America/Los_Angeles"))

if now_sd.hour != 10:
    print("Not 10AM in San Diego, exit.")
    exit()

# =============================
# 2. 读取环境变量
# =============================
SENDKEY = os.environ.get("SERVERCHAN_SENDKEY")
CITY = os.environ.get("CITY", "San Diego")
LAT = os.environ.get("LAT")
LON = os.environ.get("LON")
API_BASE = os.environ.get("GOODNIGHT_API_BASE")
USER = os.environ.get("GOODNIGHT_USER", "her")

if not SENDKEY:
    raise SystemExit("Missing SERVERCHAN_SENDKEY")

if not API_BASE:
    raise SystemExit("Missing GOODNIGHT_API_BASE")

# =============================
# 3. 获取天气（Open-Meteo）
# =============================
weather_url = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    f"&current_weather=true"
)

weather_resp = requests.get(weather_url, timeout=10)
weather_data = weather_resp.json()

temp = weather_data["current_weather"]["temperature"]
weather_code = weather_data["current_weather"]["weathercode"]

# 简单天气映射
weather_map = {
    0: "晴",
    1: "多云",
    2: "多云",
    3: "阴",
    45: "雾",
    48: "雾",
    51: "小雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
}

weather_desc = weather_map.get(weather_code, "未知")

# =============================
# 4. 获取你的网站状态
# =============================
state_url = f"{API_BASE}/state?user={USER}"

state_resp = requests.get(state_url, timeout=10)
state = state_resp.json()

# 心情
mood = state.get("mood", {})
mood_text = mood.get("text", "未记录")

# 睡眠
sleep = state.get("sleep", {})
sleep_hours = sleep.get("hours")

if sleep_hours:
    sleep_line = f"{sleep_hours}h"
else:
    sleep_line = "未同步"

# =============================
# 5. 拼接通知（只用 title）
# =============================
title = f"""{CITY} ☀

🙂 {mood_text}
🌤️ {temp}° {weather_desc}
🛌 {sleep_line}
"""

api = f"https://sctapi.ftqq.com/{SENDKEY}.send"

r = requests.post(api, data={
    "title": title
})

print(r.text)
