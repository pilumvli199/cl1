import os, json, time, redis
from typing import Dict, Any
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)
HISTORY_TTL = 7 * 3600
def push_snapshot(symbol: str, snapshot: Dict[str, Any]) -> None:
    key = f"history:{symbol}"
    r.lpush(key, json.dumps(snapshot))
    r.ltrim(key, 0, 10000)
    r.expire(key, HISTORY_TTL)
def get_latest_snapshot(symbol: str) -> Dict[str, Any]:
    key = f"history:{symbol}"
    j = r.lindex(key, 0)
    return json.loads(j) if j else {}
def push_signal(signal: Dict[str, Any]) -> None:
    r.lpush("signals:all", json.dumps(signal))
    r.ltrim("signals:all", 0, 5000)
def push_suppressed(signal: Dict[str, Any]) -> None:
    r.lpush("signals:suppressed", json.dumps(signal))
    r.ltrim("signals:suppressed", 0, 5000)
def is_in_cooldown(symbol: str, side: str) -> bool:
    return r.exists(f"cooldown:{symbol}:{side}") == 1
def set_cooldown(symbol: str, side: str, seconds: int) -> None:
    r.setex(f"cooldown:{symbol}:{side}", seconds, "1")
def increment_alert_count_for_minute() -> int:
    now_min = int(time.time() // 60)
    key = f"alerts:count:{now_min}"
    cnt = r.incr(key)
    if cnt == 1:
        r.expire(key, 70)
    return int(cnt)
