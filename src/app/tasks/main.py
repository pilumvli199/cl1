# src/app/tasks/main.py
import os
import time
import asyncio
import json
from fastapi import FastAPI
from dotenv import load_dotenv

# import project modules
from ..api_clients import binance_client
from ..datastore import redis_store as ds
from ..processors import rule_engine
from ..ai import gpt_handler

load_dotenv()

# Interval in seconds (default 1800 = 30 minutes)
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL_SECONDS", 1800))
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

app = FastAPI(title="Crypto Signal Bot")

# simple in-memory baseline (persist to Redis for production if desired)
_baseline_oi = {}


def update_baseline_if_missing(symbol: str, current_oi: float):
    if symbol not in _baseline_oi or _baseline_oi.get(symbol) == 0:
        _baseline_oi[symbol] = current_oi


async def worker_loop():
    print("Starting scheduler loop (background worker)")
    while True:
        try:
            data = binance_client.fetch_all()
            now = int(time.time())
            for sym, snap in data.items():
                if snap.get("error"):
                    print(f"[{sym}] fetch error: {snap.get('error')}")
                    continue

                ticker = snap.get("ticker", {})
                oi = snap.get("open_interest", {})

                try:
                    current_oi = float(oi.get("openInterest") or 0.0)
                except Exception:
                    current_oi = 0.0

                # persist raw snapshot to Redis history
                ds.push_snapshot(sym, {"ticker": ticker, "open_interest": oi, "ts": now})

                # ensure we have a baseline OI to compare against
                if sym not in _baseline_oi:
                    prev = ds.get_latest_snapshot(sym)
                    prev_oi = 0.0
                    try:
                        prev_oi = float(prev.get("open_interest", {}).get("openInterest") or 0.0)
                    except Exception:
                        prev_oi = 0.0
                    update_baseline_if_missing(sym, prev_oi or current_oi)

                baseline = _baseline_oi.get(sym, current_oi)
                candidate = rule_engine.evaluate_crypto(
                    {"ticker": ticker, "open_interest": oi, "ts": now},
                    baseline_oi=baseline,
                )

                # update baseline for next round (simple strategy)
                _baseline_oi[sym] = current_oi

                # call GPT handler which will call alerts.manager internally
                try:
                    res = gpt_handler.handle_candidate(candidate, {"recent_baseline_oi": baseline})
                    sent = res.get("result", {}).get("sent", False)
                except Exception as e:
                    sent = False
                    print(f"[{sym}] gpt_handler error: {e}")

                print(f"[{sym}] -> candidate {candidate.get('side')} | sent={sent}")

            await asyncio.sleep(FETCH_INTERVAL)
        except Exception as e:
            print("worker_loop error:", str(e))
            await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    # start background worker
    loop = asyncio.get_event_loop()
    loop.create_task(worker_loop())


@app.get("/health")
async def health():
    return {"status": "ok"}


# Signals endpoint: returns most recent N signals (default 50)
from fastapi.responses import JSONResponse
import json as _json


@app.get("/signals")
async def get_recent_signals(limit: int = 50):
    """Return the most recent signals stored in Redis (default 50)."""
    try:
        # Use the Redis client `r` from our redis_store module
        raw = ds.r.lrange("signals:all", 0, limit - 1)
        parsed = []
        for item in raw:
            try:
                parsed.append(_json.loads(item))
            except Exception:
                parsed.append({"raw": item})
        return JSONResponse(content={"count": len(parsed), "signals": parsed})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

