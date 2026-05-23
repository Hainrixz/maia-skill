#!/usr/bin/env python3
"""
Tododeia Trailing Stop Updater
================================
Reads the most recent history file (output/history/YYYY-MM-DD.json) and the
current market_context.json, then computes ATR-based trailing stops for every
active pick.

Trailing stop rule:
    trailing_stop = max(original_stop, current_price - N_ATR * atr_14)

Stops only MOVE UP — once a stock drops to its stop, the position closes and
is no longer tracked. The multiplier N_ATR defaults to 2.0 (configurable).

Usage:
    python3 tools/update_stops.py
    python3 tools/update_stops.py --multiplier 1.5   # tighter stops
    python3 tools/update_stops.py --history output/history/2026-05-22.json

Output:
    data/trailing_stops.json
"""

import sys
import os
import json
import glob
from datetime import datetime

SKILL_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_DIR  = os.path.join(SKILL_ROOT, "output", "history")
CONTEXT_PATH = os.path.join(SKILL_ROOT, "data", "market_context.json")
OUTPUT_PATH  = os.path.join(SKILL_ROOT, "data", "trailing_stops.json")

DEFAULT_MULTIPLIER = 2.0   # ATR × 2 = default stop distance


def load_latest_history(explicit_path: str | None = None) -> tuple[dict, str]:
    if explicit_path:
        path = explicit_path
    else:
        files = sorted(glob.glob(os.path.join(HISTORY_DIR, "*.json")))
        if not files:
            raise FileNotFoundError(f"No history files found in {HISTORY_DIR}")
        path = files[-1]

    with open(path) as f:
        data = json.load(f)
    return data, path


def load_market_context() -> dict:
    if not os.path.exists(CONTEXT_PATH):
        raise FileNotFoundError(f"market_context.json not found at {CONTEXT_PATH}\n"
                                "Run: python3 tools/pre_fetch.py")
    with open(CONTEXT_PATH) as f:
        return json.load(f)


def get_current_price(symbol: str, context: dict) -> float | None:
    """Pull the current price from market_context prices_snapshot or candidates."""
    snapshot = context.get("prices_snapshot", {})
    if symbol in snapshot:
        return snapshot[symbol].get("price")
    # Fallback: scan candidates list
    for c in context.get("candidates", []):
        if c.get("symbol") == symbol:
            return c.get("price")
    return None


def get_atr(symbol: str, context: dict) -> float | None:
    """Pull ATR-14 from candidates list or stocks dict in market_context."""
    for c in context.get("candidates", []):
        if c.get("symbol") == symbol:
            return c.get("atr_14")
    # Fallback: stocks dict
    stock = context.get("stocks", {}).get(symbol, {})
    return stock.get("atr_14")


def extract_picks(history_data: dict) -> list[dict]:
    """Return the list of picks from a history JSON.

    Supports two known history shapes:
    1. history_data["picks"] — flat list of pick dicts
    2. history_data["portfolio"]["positions"] — portfolio analysis shape
    """
    if "picks" in history_data and isinstance(history_data["picks"], list):
        return history_data["picks"]
    if "portfolio" in history_data:
        positions = history_data["portfolio"].get("positions", [])
        if positions:
            return positions
    # Last resort: look for any list-of-dicts with a "symbol" key
    for val in history_data.values():
        if isinstance(val, list) and val and isinstance(val[0], dict) and "symbol" in val[0]:
            return val
    return []


def update_trailing_stops(
    picks: list[dict],
    context: dict,
    multiplier: float = DEFAULT_MULTIPLIER,
) -> dict:
    """Compute trailing stops for all picks.

    Returns a dict keyed by symbol with stop details.
    """
    results = {}
    computed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    for pick in picks:
        symbol = pick.get("symbol") or pick.get("ticker")
        if not symbol:
            continue

        current_price = get_current_price(symbol, context)
        atr = get_atr(symbol, context)

        # Try to find the original stop in the pick data
        original_stop = (
            pick.get("stop_loss") or
            pick.get("stop") or
            pick.get("trailing_stop") or
            None
        )

        # Convert to float
        try:
            original_stop = float(original_stop) if original_stop is not None else None
        except (TypeError, ValueError):
            original_stop = None

        entry_price = pick.get("entry_price") or pick.get("price_at_fetch") or pick.get("price")
        try:
            entry_price = float(entry_price) if entry_price is not None else None
        except (TypeError, ValueError):
            entry_price = None

        # If no original stop but we have an entry and ATR, derive a reasonable stop
        if original_stop is None and entry_price and atr:
            original_stop = round(entry_price - multiplier * atr, 4)

        # Compute ATR-based trailing stop from current price
        if current_price and atr:
            atr_stop = round(current_price - multiplier * atr, 4)
        else:
            atr_stop = None

        # The trailing stop is the max of original stop and ATR-derived stop
        if original_stop is not None and atr_stop is not None:
            recommended_stop = max(original_stop, atr_stop)
            stop_raised = recommended_stop > original_stop
        elif original_stop is not None:
            recommended_stop = original_stop
            stop_raised = False
        elif atr_stop is not None:
            recommended_stop = atr_stop
            stop_raised = False
        else:
            recommended_stop = None
            stop_raised = False

        # Compute distance from current price to stop as a percentage
        stop_distance_pct = None
        if recommended_stop and current_price:
            stop_distance_pct = round((current_price - recommended_stop) / current_price * 100, 2)

        results[symbol] = {
            "symbol": symbol,
            "current_price": current_price,
            "entry_price": entry_price,
            "original_stop": original_stop,
            "atr_14": atr,
            "atr_multiplier": multiplier,
            "atr_stop": atr_stop,
            "recommended_stop": recommended_stop,
            "stop_raised": stop_raised,
            "stop_distance_pct": stop_distance_pct,
            "computed_at": computed_at,
        }

        # Status summary for console output
        status = (
            "↑ RAISED"   if stop_raised else
            "NO DATA"    if not current_price else
            "—"
        )
        price_str  = f"${current_price:.2f}"    if current_price   else "N/A"
        stop_str   = f"${recommended_stop:.2f}" if recommended_stop else "N/A"
        dist_str   = f"{stop_distance_pct:.1f}%" if stop_distance_pct else "N/A"
        print(f"  {symbol:<6}  price={price_str:<9}  stop={stop_str:<9}  dist={dist_str:<7}  {status}")

    return results


def main():
    args = sys.argv[1:]
    history_path = None
    multiplier = DEFAULT_MULTIPLIER

    i = 0
    while i < len(args):
        if args[i] == "--history" and i + 1 < len(args):
            history_path = args[i + 1]
            i += 2
        elif args[i] == "--multiplier" and i + 1 < len(args):
            multiplier = float(args[i + 1])
            i += 2
        else:
            i += 1

    print(f"[update_stops] {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}")

    history_data, used_path = load_latest_history(history_path)
    print(f"[update_stops] History file: {os.path.basename(used_path)}")

    context = load_market_context()
    context_ts = context.get("generated_at", "unknown")
    print(f"[update_stops] Market context: {context_ts}  (ATR multiplier: {multiplier}x)")

    picks = extract_picks(history_data)
    if not picks:
        print("[update_stops] ⚠ No picks found in history file.")
        sys.exit(0)

    print(f"[update_stops] Computing stops for {len(picks)} picks:")
    results = update_trailing_stops(picks, context, multiplier=multiplier)

    raised  = sum(1 for v in results.values() if v.get("stop_raised"))
    no_data = sum(1 for v in results.values() if not v.get("current_price"))

    output = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "history_file": os.path.basename(used_path),
        "atr_multiplier": multiplier,
        "picks_total": len(picks),
        "stops_raised": raised,
        "stops_no_data": no_data,
        "stops": results,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n[update_stops] ✓ {raised}/{len(picks)} stops raised  ({no_data} missing market data)")
    print(f"[update_stops] ✓ Written → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
