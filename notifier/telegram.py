import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

STATUS_ICON = {
    "BLOCK": "BLOCKED",
    "WARN":  "WARNING",
    "PASS":  "PASSED",
}

def send(project_name, scan_id, gate):
    if not BOT_TOKEN or not CHAT_ID:
        print("[Telegram] Credentials not set — skipping")
        return

    counts = gate["counts"]
    result = gate["result"]
    icon   = STATUS_ICON.get(result, result)

    reasons = "\n".join([f"- {r}" for r in gate["reasons"]]) or "- No blocking issues"

    message = (
        f"SHIELDPIPE SECURITY SCAN\n"
        f"{'=' * 30}\n"
        f"Project : {project_name}\n"
        f"Scan ID : {scan_id[:8]}\n"
        f"Status  : {icon}\n"
        f"\n"
        f"FINDINGS\n"
        f"Critical : {counts['CRITICAL']}\n"
        f"High     : {counts['HIGH']}\n"
        f"Medium   : {counts['MEDIUM']}\n"
        f"Low      : {counts['LOW']}\n"
        f"\n"
        f"REASONS\n"
        f"{reasons}\n"
        f"{'=' * 30}\n"
        f"Dashboard: http://localhost:5002"
    )

    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id":    CHAT_ID,
            "text":       message,
            "parse_mode": "HTML"
        }, timeout=10)
        print("[Telegram] Alert sent")
    except Exception as e:
        print(f"[Telegram] Error: {e}")