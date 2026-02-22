import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# 判断当前是否 San Diego 时间 10:00
now_sd = datetime.now(ZoneInfo("America/Los_Angeles"))

if now_sd.hour != 10:
    print("Not 10AM in San Diego, exit.")
    exit()
# ====== 读取环境变量 ======
SENDKEY = os.environ.get("SERVERCHAN_SENDKEY")
API_BASE = os.environ.get("GOODNIGHT_API_BASE")
CITY = os.environ.get("CITY")
LAT = os.environ.get("LAT")
LON = os.environ.get("LON")

if not SENDKEY:
    raise SystemExit("Missing SERVERCHAN_SENDKEY")

# ====== 1. 获取心情 ======
state_url = f"{API_BASE}/state?user=her"
state_resp = requests.get(state_url)
state = state_resp.json()

mood = state.get("mood", {})
mood_text = mood.get("text", "未记录")

# ====== 2. 获取天气（Open-Meteo） ======
weather_url = (
    f"https://api.open-meteo.com/v1/forecast?"
    f"latitude={LAT}&longitude={LON}"
    "&current=temperature_2m,weather_code"
)
weather_resp = requests.get(weather_url)
weather = weather_resp.json()

temp = weather.get("current", {}).get("temperature_2m", "N/A")

def weather_text(code):
    mapping = {
        0: "晴",
        1: "大致晴",
        2: "多云",
        3: "阴",
        61: "小雨",
        63: "中雨",
        65: "大雨"
    }
    return mapping.get(code, "未知")

code = weather.get("current", {}).get("weather_code", -1)
weather_desc = weather_text(code)

# ====== 3. 拼接推送内容 ======
title = f"{CITY} 早安"

desp = f"""🌤️ 天气：{weather_desc} {temp}°

🙂 心情：{mood_text}

🏃 运动提醒：记得拉伸

"""
sleep = state.get("sleep", {})
sleep_hours = sleep.get("hours")

if sleep_hours:
    sleep_line = f"🛌 睡眠：{sleep_hours}h"
else:
    sleep_line = "🛌 睡眠：还未同步"
    
# ====== 4. 发送到 Server酱 ======
api = f"https://sctapi.ftqq.com/{SENDKEY}.send"

r = requests.post(api, data={
    "title": title,
    "desp": desp
})

print(r.text)
