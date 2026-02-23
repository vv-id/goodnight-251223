import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# =============================
# 1. 只在 San Diego 10:00 发送（自动适配夏令时）
# =============================
now_sd = datetime.now(ZoneInfo("America/Los_Angeles"))
#if now_sd.hour != 10:
    #print("Not 10AM in San Diego, exit.")
    #raise SystemExit(0)

# =============================
# 2. 环境变量
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
# 3. 获取天气（Open-Meteo）
# =============================
weather_url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&current_weather=true"
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

# 体感和温度格式化
def fmt_num(x):
    return "N/A" if x is None else str(int(round(float(x))))

temp_s = fmt_num(temp)
feels_s = fmt_num(feels)
tmax_s = fmt_num(tmax)
tmin_s = fmt_num(tmin)

# =============================
# 4. 获取状态：只用心情 + 睡眠（不出现人称）
# =============================
state_url = f"{API_BASE}/state?user={USER}"

print("Requesting URL:", state_url)  # 打印出请求的 URL，确认是否正确

try:
    response = requests.get(state_url, timeout=10)
    print("Response content:", response.text)  # 打印返回的原始文本内容
    state = response.json()  # 尝试解析返回的 JSON
except ValueError as e:
    print("Failed to parse JSON. Response content:", response.text)  # 如果解析失败，打印响应内容
    state = {}  # 返回空字典
except requests.exceptions.RequestException as e:
    print("Request failed:", e)  # 如果请求出错，打印错误信息
    state = {}

# =============================
# 5. 拼接通知（只用 title，多行）
# =============================
mood_text = (state.get("mood") or {}).get("text", "未记录")
sleep_hours = (state.get("sleep") or {}).get("hours")
sleep_line = f"{sleep_hours}h" if sleep_hours else "未同步"

title = f"""{CITY} {emoji}\n\n
🙂 {mood_text}\n
{emoji} {temp_s}° 体感{feels_s}°  ↑{tmax_s}° ↓{tmin_s}°\n
🛌 {sleep_line}
"""

# =============================
# 6. 发送到 Server酱
# =============================
api = f"https://sctapi.ftqq.com/{SENDKEY}.send"
r = requests.post(api, data={"title": title}, timeout=10)
print(r.text)  # 打印响应内容，帮助调试

