import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


def safe_get_json(url: str, timeout: int = 10, headers: dict | None = None):
    """
    安全获取 JSON：
    - 返回 (data, status_code, text_snippet)
    - 如果不是 JSON，就返回 (None, status_code, 前 300 字符)
    """
    resp = requests.get(url, timeout=timeout, headers=headers)
    text = resp.text or ""
    try:
        return resp.json(), resp.status_code, text[:300]
    except Exception:
        return None, resp.status_code, text[:300]


def fmt_num(x):
    try:
        return "N/A" if x is None else str(int(round(float(x))))
    except Exception:
        return "N/A"


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


# =============================
# 1) San Diego 时间（自动适配夏令时）
# =============================
now_sd = datetime.now(ZoneInfo("America/Los_Angeles"))

# 如果你想只在 10 点发送，打开下面三行（现在先别开，先把流程跑通）
# if now_sd.hour != 10:
#     print("Not 10AM in San Diego, exit.")
#     raise SystemExit(0)

# =============================
# 2) 环境变量
# =============================
SENDKEY = os.environ.get("SERVERCHAN_SENDKEY")
CITY = os.environ.get("CITY", "San Diego")
LAT = os.environ.get("LAT")
LON = os.environ.get("LON")
API_BASE = os.environ.get("GOODNIGHT_API_BASE")
USER = os.environ.get("GOODNIGHT_USER", "state")  # 你说不要人称，就用 state 当默认值

if not SENDKEY:
    raise SystemExit("Missing SERVERCHAN_SENDKEY")
if not (LAT and LON):
    raise SystemExit("Missing LAT/LON")
if not API_BASE:
    raise SystemExit("Missing GOODNIGHT_API_BASE")

# =============================
# 3) 天气：体感 + 今日高低 + emoji（Open-Meteo，无 key）
# =============================
weather_url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&current=temperature_2m,apparent_temperature,weather_code"
    "&daily=temperature_2m_max,temperature_2m_min"
    "&timezone=America/Los_Angeles"
)

w, w_status, w_snip = safe_get_json(weather_url, timeout=10)

if not w:
    # 天气 API 失败也别让整个脚本死掉
    print(f"[WARN] Weather API not JSON. status={w_status}, body_snip={w_snip}")
    temp_s = feels_s = tmax_s = tmin_s = "N/A"
    weather_desc, emoji = "未知", "❓"
else:
    cur = w.get("current", {}) or {}
    daily = w.get("daily", {}) or {}

    temp = cur.get("temperature_2m")
    feels = cur.get("apparent_temperature")
    code = cur.get("weather_code")

    tmax = (daily.get("temperature_2m_max") or [None])[0]
    tmin = (daily.get("temperature_2m_min") or [None])[0]

    weather_desc, emoji = code_to_desc_and_emoji(code)

    temp_s = fmt_num(temp)
    feels_s = fmt_num(feels)
    tmax_s = fmt_num(tmax)
    tmin_s = fmt_num(tmin)

# =============================
# 4) 获取状态：心情 + 睡眠
# =============================
state_url = f"{API_BASE}/state?user={USER}"
state, s_status, s_snip = safe_get_json(state_url, timeout=10)

if not state:
    # 这里就是你现在炸的地方：不是 JSON
    print(f"[WARN] State API not JSON. status={s_status}, body_snip={s_snip}")
    mood_text = "未记录"
    sleep_line = "未同步"
else:
    mood_text = ((state.get("mood") or {}).get("text")) or "未记录"
    sleep_hours = (state.get("sleep") or {}).get("hours")
    sleep_line = f"{sleep_hours}h" if sleep_hours else "未同步"

# =============================
# 5) Server酱推送：title 单行，正文放 desp（避免你说的“乱码/挤成一团”）
# =============================
title = f"{CITY} {emoji} 早安"
desp = (
    f"🙂 {mood_text}\n\n"
    f"{emoji} {weather_desc}  {temp_s}°C（体感 {feels_s}°C）\n"
    f"↑{tmax_s}°C  ↓{tmin_s}°C\n\n"
    f"🛌 {sleep_line}\n\n"
    f"🕙 San Diego：{now_sd.strftime('%Y-%m-%d %H:%M')}"
)

api = f"https://sctapi.ftqq.com/{SENDKEY}.send"
r = requests.post(api, data={"title": title, "desp": desp}, timeout=10)

print("[INFO] ServerChan response:")
print(r.status_code, r.text)
