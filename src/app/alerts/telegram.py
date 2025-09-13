import os, time, requests
from typing import Dict
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
def _build_message(signal: Dict) -> str:
    ts = time.localtime(signal.get("ts", time.time()))
    return (
        f"🚨 Signal: {signal.get('symbol')}\n"
        f"Action: {signal.get('side')}  |  Confidence: {signal.get('confidence')}%\n"
        f"Reason: {signal.get('reasoning','-')}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', ts)}"
    )
def send_telegram(signal: Dict, max_retries: int = 3, backoff_seconds: int = 2) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print('telegram: missing config')
        return False
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': _build_message(signal),
               'parse_mode': 'HTML', 'disable_web_page_preview': True}
    attempt = 0
    while attempt < max_retries:
        try:
            resp = requests.post(TELEGRAM_API, json=payload, timeout=6)
            if resp.status_code == 200:
                return True
            attempt += 1
            time.sleep(backoff_seconds * attempt)
        except Exception:
            attempt += 1
            time.sleep(backoff_seconds * attempt)
    print('telegram: failed after retries')
    return False
