import os
import sys
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =============================
# 0) 时间控制：只在本地 9:00 或 10:00 执行
# =============================
TZ_LOCAL = os.environ.get("LOCAL_TZ", "America/Los_Angeles")
PUSH_HOUR_LOCAL = int(os.environ.get("PUSH_HOUR_LOCAL", "10"))

now_local = datetime.now(ZoneInfo(TZ_LOCAL))
now_utc = datetime.now(ZoneInfo("UTC"))

# 只在本地 9:00 或 10:00 执行推送
#if now_local.hour not in [9, 10]:
    #print(f"[SKIP] Local time is {now_local:%Y-%m-%d %H:%M:%S %Z}, not 9:00 or 10:00")
    #sys.exit(0)

# 打印日志，方便调试
print(f"[PASS] Local={now_local:%H:%M}, UTC={now_utc:%H:%M}")

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

MOOD = (os.environ.get("MOOD") or "").strip()
EXERCISE_TIP = (os.environ.get("EXERCISE_TIP") or "").strip()

# =============================
# 2) 天气：Open-Meteo（无需 key）
# =============================
def weather_code_to_text(code: int) -> str:
    mapping = {
        0: "晴朗",
        1: "大部晴朗",
        2: "局部多云",
        3: "阴",
        45: "雾",
        48: "冻雾",
        51: "小雨",
        53: "中雨",
        55: "大雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        80: "阵雨",
        81: "阵雨",
        82: "暴雨",
        95: "雷暴",
    }
    return mapping.get(code, "天气变化")

def weather_emoji(code: int) -> str:
    if code in (0, 1, 2):
        return "☀️"
    if code == 3:
        return "☁️"
    if code in (45, 48):
        return "🌫️"
    if 51 <= code <= 67 or 80 <= code <= 82:
        return "🌧️"
    if 71 <= code <= 77:
        return "❄️"
    if code >= 95:
        return "⛈️"
    return "🌤️"

def fetch_weather(lat, lon, tz):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "temperature_unit": "celsius",
        "current": "temperature_2m,apparent_temperature,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    cur = data["current"]
    daily = data["daily"]

    return (
        float(cur["temperature_2m"]),
        float(cur["apparent_temperature"]),
        int(cur["weather_code"]),
        float(daily["temperature_2m_max"][0]),
        float(daily["temperature_2m_min"][0]),
    )

temp, feels, wcode, tmax, tmin = fetch_weather(LAT, LON, TZ_LOCAL)

# =============================
# 3) 浪漫风格一句话生成
# =============================
def romantic_line(code, feels_temp):
    if 51 <= code <= 67 or 80 <= code <= 82:
        return "今天可能会下雨，记得带伞。有人希望你别淋到。"
    if feels_temp < 8:
        return "今天有点冷，记得多穿一点。温度低，但有人在想你。"
    if feels_temp > 30:
        return "天气有点热，注意补水。别太逞强。"
    if code in (0, 1, 2):
        return "阳光不错，愿你今天也有一点轻松。"
    return "慢慢来的一天，也很好。"

soft_line = romantic_line(wcode, feels)

mood_line = MOOD if MOOD else "😊 平静而温柔"
exercise_line = EXERCISE_TIP if EXERCISE_TIP else "多运动，注意拉伸噢～"

# =============================
# 4) 组装内容
# =============================
title = f"{CITY} 今日提醒 {weather_emoji(wcode)}"

# 生成卡片预览摘要
short = (
    f"{weather_emoji(wcode)} {wcode}｜{temp:.1f}°C "
    f"(体感{feels:.1f})｜H{tmax:.1f} L{tmin:.1f}｜"
    f"{mood_line}"
)

# 生成详情页
desp = f"""## {weather_emoji(wcode)} {CITY} 今日提醒

### 🌤️ 今日天气
- **{weather_code_to_text(wcode)}**
- **当前：{temp:.1f}°C ｜ 体感：{feels:.1f}°C**
- **最高：{tmax:.1f}°C ｜ 最低：{tmin:.1f}°C**

---

### 🌙 一句话
> {soft_line}

---

### 😊 心情
> {mood_line}

---

### 🏃 今日小提醒
- {exercise_line}

---

_🕙 {now_local:%Y-%m-%d %H:%M %Z}_
"""

# =============================
# 5) 推送到 Server酱
# =============================
push_url = f"https://sctapi.ftqq.com/{SENDKEY}.send"
payload = {
    "title": title,
    "short": short,
    "desp": desp,
}

resp = requests.post(push_url, data=payload, timeout=20)
resp.raise_for_status()

j = resp.json()
print("[ServerChan Response]", j)

if j.get("code") != 0:
    raise SystemExit("Push failed")

print("[OK] Push sent.")

