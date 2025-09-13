import time, json
from typing import Any, Dict
from .gpt_client import call_model
from ..alerts.manager import handle_signal
from ..datastore import redis_store as ds
def parse_model_output(raw_output: Any) -> Dict[str, Any]:
    if isinstance(raw_output, dict):
        data = raw_output
    else:
        try:
            data = json.loads(raw_output)
        except Exception:
            return {"symbol": None, "side": "HOLD", "confidence": 0,
                    "reasoning": f"unparseable_model_output:{str(raw_output)[:200]}", "ts": int(time.time())}
    side = (data.get("side") or "").upper()
    if side not in ("BUY","SELL","HOLD"):
        side = "HOLD"
    try:
        conf = int(round(float(data.get("confidence", 0))))
    except Exception:
        conf = 0
    return {"symbol": data.get("symbol"), "side": side, "confidence": max(0,min(100,conf)),
            "reasoning": data.get("reasoning","")[:1000], "ts": int(time.time())}
def handle_candidate(candidate: Dict[str, Any], aggregates: Dict[str, Any]):
    model_out = call_model(candidate, aggregates)
    signal = parse_model_output(model_out)
    ds.push_signal({**signal, "model_raw": model_out})
    res = handle_signal(signal)
    return {"signal": signal, "result": res}
