import os
import requests

SENDKEY = os.environ.get("SERVERCHAN_SENDKEY")

if not SENDKEY:
    raise SystemExit("Missing SERVERCHAN_SENDKEY")

api = f"https://sctapi.ftqq.com/{SENDKEY}.send"

r = requests.post(api, data={
    "title": "测试推送成功 🎉",
    "desp": "如果你看到这条消息，说明 GitHub Actions 已经能正常给你发微信了。"
})

print(r.text)
