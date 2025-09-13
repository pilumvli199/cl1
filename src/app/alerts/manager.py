import os, time
from typing import Dict
from ..datastore import redis_store as ds
from .telegram import send_telegram
CONFIDENCE_THRESHOLD = int(os.getenv('CONFIDENCE_THRESHOLD', 60))
COOLDOWN_SECONDS = int(os.getenv('COOLDOWN_SECONDS', 600))
GLOBAL_RATE_LIMIT = int(os.getenv('GLOBAL_RATE_LIMIT', 20))
def should_send_alert(signal: Dict) -> bool:
    side = (signal.get('side') or '').upper()
    if side not in ('BUY','SELL'):
        return False
    if int(signal.get('confidence',0)) < CONFIDENCE_THRESHOLD:
        return False
    symbol = signal.get('symbol')
    if not symbol:
        return False
    if ds.is_in_cooldown(symbol, side):
        return False
    cnt = ds.increment_alert_count_for_minute()
    if cnt > GLOBAL_RATE_LIMIT:
        return False
    return True
def handle_signal(signal: Dict) -> Dict:
    signal['ts'] = signal.get('ts') or int(time.time())
    ds.push_signal(signal)
    if should_send_alert(signal):
        ok = send_telegram(signal)
        if ok:
            ds.set_cooldown(signal['symbol'], signal['side'], COOLDOWN_SECONDS)
            return {'sent': True, 'reason': 'sent'}
        else:
            ds.push_suppressed({**signal, 'suppressed_reason': 'telegram_failed'})
            return {'sent': False, 'reason': 'telegram_failed'}
    else:
        ds.push_suppressed({**signal, 'suppressed_reason': 'filtered_or_hold'})
        return {'sent': False, 'reason': 'filtered_or_hold'}
