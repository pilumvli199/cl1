from typing import Dict, Any
def calc_pct(a, b):
    try:
        a = float(a); b = float(b)
        if b == 0:
            return 0.0
        return (a - b) / abs(b) * 100.0
    except Exception:
        return 0.0
OI_SPIKE_PCT_THRESHOLD = 8.0
PRICE_MOVE_PCT_THRESHOLD = 1.5
def evaluate_crypto(snapshot: Dict[str, Any], baseline_oi: float = None) -> Dict[str, Any]:
    ticker = snapshot.get("ticker") or {}
    oi = snapshot.get("open_interest") or {}
    symbol = ticker.get("symbol") or oi.get("symbol")
    price_change_pct = float(ticker.get("priceChangePercent") or 0.0)
    try:
        current_oi = float(oi.get("openInterest") or 0.0)
    except Exception:
        current_oi = 0.0
    if baseline_oi and baseline_oi > 0:
        oi_pct = calc_pct(current_oi, baseline_oi)
    else:
        oi_pct = 0.0
    if oi_pct >= OI_SPIKE_PCT_THRESHOLD and price_change_pct >= PRICE_MOVE_PCT_THRESHOLD:
        return {
            "symbol": symbol,
            "side": "BUY",
            "confidence": min(95, int(50 + (oi_pct / 2) + (price_change_pct))),
            "reasoning": f"OI +{oi_pct:.1f}% and price +{price_change_pct:.2f}%"
        }
    if oi_pct >= OI_SPIKE_PCT_THRESHOLD and price_change_pct <= -PRICE_MOVE_PCT_THRESHOLD:
        return {
            "symbol": symbol,
            "side": "SELL",
            "confidence": min(95, int(50 + (oi_pct / 2) + abs(price_change_pct))),
            "reasoning": f"OI +{oi_pct:.1f}% and price {price_change_pct:.2f}%"
        }
    return {
        "symbol": symbol,
        "side": "HOLD",
        "confidence": 0,
        "reasoning": "no significant OI/price signal"
    }
