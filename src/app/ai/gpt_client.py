    import os, openai, time
    from typing import Dict, Any
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
    def build_prompt(signal_candidate: Dict[str, Any], recent_aggregates: Dict[str, Any]) -> str:
        return (
            "You are a concise trading assistant. Given the candidate and recent aggregates, "
            "answer in JSON {"symbol":"","side":"BUY|SELL|HOLD","confidence":0-100,"reasoning":"..."}.

"
            f"Candidate: {signal_candidate}\n\nAggregates: {recent_aggregates}\n\n"
            "Return only valid JSON with keys: symbol, side, confidence, reasoning."
        )
    def call_model(signal_candidate: Dict[str, Any], recent_aggregates: Dict[str, Any], max_tokens: int = 150) -> Dict[str, Any]:
        if not OPENAI_API_KEY:
            out = {
                "symbol": signal_candidate.get("symbol"),
                "side": signal_candidate.get("side"),
                "confidence": signal_candidate.get("confidence", 0),
                "reasoning": signal_candidate.get("reasoning", "")
            }
            return out
        prompt = build_prompt(signal_candidate, recent_aggregates)
        resp = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role":"system","content":"You are a concise trading assistant."},
                      {"role":"user","content":prompt}],
            max_tokens=max_tokens,
            temperature=0.0
        )
        text = resp["choices"][0]["message"]["content"]
        try:
            import json
            parsed = json.loads(text)
            return parsed
        except Exception:
            return {
                "symbol": signal_candidate.get("symbol"),
                "side": signal_candidate.get("side"),
                "confidence": signal_candidate.get("confidence", 0),
                "reasoning": signal_candidate.get("reasoning", "") + " (model-unparseable)"
            }
