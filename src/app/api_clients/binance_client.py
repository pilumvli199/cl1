import time, requests
from typing import Dict, Any
BASE_FUTURES = "https://fapi.binance.com"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
def get_24hr_ticker(symbol: str) -> Dict[str, Any]:
    url = f"{BASE_FUTURES}/fapi/v1/ticker/24hr"
    resp = requests.get(url, params={"symbol": symbol}, timeout=6)
    resp.raise_for_status()
    return resp.json()
def get_open_interest(symbol: str) -> Dict[str, Any]:
    url = f"{BASE_FUTURES}/fapi/v1/openInterest"
    resp = requests.get(url, params={"symbol": symbol}, timeout=6)
    resp.raise_for_status()
    return resp.json()
def fetch_all() -> Dict[str, Dict[str, Any]]:
    out = {}
    for s in SYMBOLS:
        try:
            ticker = get_24hr_ticker(s)
            oi = get_open_interest(s)
            out[s] = {"ticker": ticker, "open_interest": oi, "ts": int(time.time())}
        except Exception as e:
            out[s] = {"error": str(e)}
    return out
