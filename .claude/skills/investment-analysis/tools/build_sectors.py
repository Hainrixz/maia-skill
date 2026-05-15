#!/usr/bin/env python3
"""
build_sectors.py — Generate Block 1 (sectors JSON) deterministically from pre-fetched data.

No LLM required. Reads market_context.json + news_context.json and outputs
a structured sectors dict that matches the schema expected by write_report.py.

Usage:
    python3 tools/build_sectors.py
    python3 tools/build_sectors.py --out /tmp/sectors.json
    python3 tools/build_sectors.py --enrich-picks /tmp/strategy_picks.json
    python3 tools/build_sectors.py --out /tmp/sectors.json --enrich-picks /tmp/picks.json

The --enrich-picks option takes the risk_adjusted_picks array (JSON file or pipe)
and overlays each pick's recommendation + reasoning onto the matching sector asset.

Exit codes:
    0  success
    1  missing required input files
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKET_CTX_PATH = os.path.join(SKILL_DIR, "data", "market_context.json")
NEWS_CTX_PATH = os.path.join(SKILL_DIR, "data", "news_context.json")

# Map from pre_fetch correlation_group values → report sector key
MATERIALS_GROUPS = {"energy", "base_metals", "precious_metals"}
# All other groups fall under 'stocks' sector

# Sector summaries and outlooks are generated programmatically from macro data
# Static name map for common tickers (fallback if not in context)
TICKER_NAMES: dict[str, str] = {
    "META": "Meta Platforms", "NFLX": "Netflix", "PYPL": "PayPal Holdings",
    "SOFI": "SoFi Technologies", "WFC": "Wells Fargo", "C": "Citigroup",
    "JNJ": "Johnson & Johnson", "AMGN": "Amgen", "MA": "Mastercard",
    "MELI": "MercadoLibre", "FCX": "Freeport-McMoRan", "XOM": "ExxonMobil",
    "GLD": "SPDR Gold Trust", "GDX": "VanEck Gold Miners ETF",
    "OXY": "Occidental Petroleum", "COP": "ConocoPhillips", "CVX": "Chevron",
    "NEM": "Newmont", "SLV": "iShares Silver Trust", "KMI": "Kinder Morgan",
    "AAPL": "Apple", "GOOGL": "Alphabet", "MSFT": "Microsoft", "AMZN": "Amazon",
    "NVDA": "NVIDIA", "AMD": "AMD", "TSLA": "Tesla", "V": "Visa",
    "BAC": "Bank of America", "JPM": "JPMorgan Chase",
    "ABBV": "AbbVie", "LLY": "Eli Lilly", "REGN": "Regeneron",
    "NU": "Nu Holdings", "SNOW": "Snowflake", "CRM": "Salesforce",
    "AVGO": "Broadcom", "ARM": "Arm Holdings",
}

SECTOR_SUMMARY_TEMPLATE = {
    "stocks": (
        "US equities screened from the {n_assets}-candidate universe. "
        "Regime: {regime}. VIX={vix:.1f}, Fear&Greed={fg} ({fg_label}). "
        "SPY RSI={spy_rsi:.0f} — {spy_signal}. "
        "Top entry opportunities by RSI oversold + fundamental quality shown below."
    ),
    "materials": (
        "Commodities and materials equities screened from the pre-fetch universe. "
        "Gold/energy/base-metals candidates with RSI and valuation data from yfinance. "
        "Regime: {regime}. Macro signal: {macro_signal}."
    )
}


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_nested(d: dict, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
        if d is None:
            return default
    return d


def fmt_price(val) -> str:
    if val is None:
        return "N/A"
    try:
        return f"${float(val):.2f}"
    except (TypeError, ValueError):
        return "N/A"


def fmt_pct(val) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def build_asset(sym: str, candidate: dict, snap: dict, news_data: dict) -> dict | None:
    """Build a report asset object from a candidate dict + prices_snapshot + news."""
    pr = (
        candidate.get("price") or candidate.get("price_at_fetch")
        or snap.get(sym, {}).get("price", 0) or 0
    )
    if not pr:
        return None
    rsi = candidate.get("rsi") or 0
    trend = candidate.get("trend") or "mixed"
    entry_quality = candidate.get("entry_quality") or "N/A"
    forward_pe = candidate.get("forward_pe")
    peg = candidate.get("peg")
    rev_growth = candidate.get("revenue_growth_yoy")
    fcf_margin = candidate.get("fcf_margin")

    # Key support/resistance: rough estimate from 52w range
    range_pct = candidate.get("range_52w_pct") or 25  # default 25% range
    key_support = round(pr * (1 - range_pct / 200), 2)
    key_resistance = round(pr * (1 + range_pct / 200), 2)

    nn = news_data.get(sym) or {}
    raw_headlines = nn.get("key_news") or []
    headlines = [h.get("title", "")[:80] for h in raw_headlines[:2]]
    while len(headlines) < 2:
        headlines.append("No additional headlines available")

    sentiment = get_nested(nn, "sentiment", "label", default="neutral")

    name = TICKER_NAMES.get(sym) or candidate.get("name") or sym

    return {
        "name": name,
        "symbol": sym,
        "watchlist": candidate.get("correlation_group") or "unknown",
        "current_price": fmt_price(pr),
        "change_24h": "N/A",
        "change_7d": "N/A",
        "change_30d": "N/A",
        "ytd_change": "N/A",
        "week_52_high": fmt_price(key_resistance),
        "week_52_low": fmt_price(key_support),
        "market_cap": "N/A",
        "volume_24h": "N/A",
        "sentiment": sentiment,
        "social_sentiment": sentiment,
        "social_buzz": "medium",
        "confidence": 7,
        "source_agreement": "high",
        "key_news": headlines,
        "social_highlights": [
            "Pre-screened via yfinance universe",
            f"Entry quality: {entry_quality}",
        ],
        "recommendation": "N/A",
        "reasoning": entry_quality,
        "technicals": {
            "trend": trend,
            "rsi": rsi,
            "macd": "N/A",
            "key_support": key_support,
            "key_resistance": key_resistance,
            "entry_quality": entry_quality,
        },
        "valuation": {
            "pe": None,
            "forward_pe": forward_pe,
            "peg": peg,
            "ev_ebitda": None,
            "verdict": f"PEG={peg:.2f}" if peg else "Pre-fetched from yfinance",
        },
        "fundamentals": {
            "revenue_growth": fmt_pct(rev_growth),
            "gross_margin": "N/A",
            "fcf_margin": fmt_pct(fcf_margin),
            "debt_equity": None,
            "verdict": "Pre-fetched from yfinance",
        },
    }


def infer_spy_signal(rsi: float) -> str:
    if rsi >= 70:
        return "overbought — stagger equity entries"
    if rsi <= 30:
        return "oversold — index dip opportunity"
    return "neutral"


def infer_macro_signal(regime: str) -> str:
    mapping = {
        "RISK_ON": "risk-on regime — growth assets favored",
        "RISK_OFF": "risk-off regime — safe havens favored",
        "MIXED": "mixed regime — sector-selective approach recommended",
    }
    return mapping.get(regime.upper() if regime else "", "mixed signals")


def build_sectors(ctx: dict, news: dict, ts: str) -> dict:
    snap = ctx.get("prices_snapshot") or {}
    candidates = ctx.get("candidates") or []
    macro = ctx.get("macro") or {}

    vix = macro.get("vix") or 0
    fg = macro.get("fear_greed_value") or macro.get("fear_greed", {}).get("value") or 0
    fg_label = macro.get("fear_greed_label") or macro.get("fear_greed", {}).get("label") or "N/A"
    regime = macro.get("regime") or "MIXED"
    spy_rsi = get_nested(snap, "SPY", "technicals", "rsi", default=0)

    news_data = news.get("news") or {}

    # Build lookup: symbol → correlation_group from candidates list
    sym_to_group: dict[str, str] = {}
    for c in candidates:
        sym = c.get("symbol")
        group = c.get("correlation_group") or c.get("watchlist") or c.get("group") or "unknown"
        if sym:
            sym_to_group[sym] = group

    # Group by report sector — candidates are already sorted best-first by pre_fetch.py
    stocks_syms: list[tuple[str, str]] = []
    materials_syms: list[tuple[str, str]] = []

    seen = set()
    for c in candidates:
        sym = c.get("symbol")
        if not sym or sym in seen:
            continue
        seen.add(sym)
        group = sym_to_group.get(sym, "unknown")
        if group in MATERIALS_GROUPS:
            materials_syms.append((sym, group))
        else:
            stocks_syms.append((sym, group))

    # Build candidate lookup: symbol → candidate dict
    sym_to_candidate: dict[str, dict] = {c["symbol"]: c for c in candidates if c.get("symbol")}

    # Build asset objects
    def build_group(sym_wl_pairs):
        assets = []
        for sym, _wl in sym_wl_pairs:
            cand = sym_to_candidate.get(sym, {})
            a = build_asset(sym, cand, snap, news_data)
            if a:
                assets.append(a)
        return assets

    stocks_assets = build_group(stocks_syms)
    materials_assets = build_group(materials_syms)

    # Sector summaries
    n_stock_assets = len(stocks_assets)
    spy_signal = infer_spy_signal(spy_rsi)
    macro_signal = infer_macro_signal(regime)

    stocks_summary = SECTOR_SUMMARY_TEMPLATE["stocks"].format(
        n_assets=n_stock_assets, regime=regime, vix=float(vix),
        fg=fg, fg_label=fg_label, spy_rsi=float(spy_rsi), spy_signal=spy_signal
    )
    materials_summary = SECTOR_SUMMARY_TEMPLATE["materials"].format(
        regime=regime, macro_signal=macro_signal
    )

    # Top pick placeholders — will be overwritten by --enrich-picks if available
    stocks_top = stocks_assets[0]["symbol"] if stocks_assets else "N/A"
    materials_top = materials_assets[0]["symbol"] if materials_assets else "N/A"

    return {
        "stocks": {
            "sector": "stocks",
            "timestamp": ts,
            "sector_summary": stocks_summary,
            "sector_outlook": _infer_outlook(regime, spy_rsi),
            "top_pick": stocks_top,
            "top_pick_reasoning": f"Highest ranked by entry quality in screened universe (RSI={stocks_assets[0]['technicals']['rsi']:.0f})" if stocks_assets else "N/A",
            "assets": stocks_assets,
        },
        "materials": {
            "sector": "materials",
            "timestamp": ts,
            "sector_summary": materials_summary,
            "sector_outlook": "bullish" if macro.get("gold_trend") == "up" else "neutral",
            "top_pick": materials_top,
            "top_pick_reasoning": f"Highest ranked materials asset in screened universe" if materials_assets else "N/A",
            "assets": materials_assets,
        },
    }


def _infer_outlook(regime: str, spy_rsi: float) -> str:
    if regime == "RISK_ON" and spy_rsi < 70:
        return "bullish"
    if regime == "RISK_OFF":
        return "bearish"
    return "neutral"


def enrich_with_picks(sectors: dict, picks: list) -> dict:
    """Overlay recommendation + reasoning from strategy picks onto sector assets."""
    # Build lookup: symbol → pick
    pick_map = {p["symbol"]: p for p in picks if p.get("symbol")}

    for sector_key, sector_data in sectors.items():
        assets = sector_data.get("assets") or []
        top_pick_sym = None
        top_pick_score = -1

        for asset in assets:
            sym = asset.get("symbol")
            if sym and sym in pick_map:
                pick = pick_map[sym]
                asset["recommendation"] = pick.get("recommendation", "buy")
                asset["reasoning"] = pick.get("reasoning", asset["reasoning"])
                asset["confidence"] = pick.get("confidence", asset["confidence"])
                # Track top pick by risk_adjusted_score
                score = pick.get("risk_adjusted_score", 0)
                if score > top_pick_score:
                    top_pick_score = score
                    top_pick_sym = sym

        if top_pick_sym:
            sector_data["top_pick"] = top_pick_sym
            pick = pick_map[top_pick_sym]
            sector_data["top_pick_reasoning"] = pick.get("reasoning", "Top ranked by risk-adjusted score")

    return sectors


def main():
    parser = argparse.ArgumentParser(description="Build sectors JSON from pre-fetched data")
    parser.add_argument(
        "--out", default=None,
        help="Output path for sectors JSON (default: print to stdout)"
    )
    parser.add_argument(
        "--enrich-picks", default=None, metavar="PICKS_JSON",
        help="Path to JSON file containing risk_adjusted_picks array to overlay on assets"
    )
    args = parser.parse_args()

    ctx = load_json(MARKET_CTX_PATH)
    news = load_json(NEWS_CTX_PATH) if os.path.exists(NEWS_CTX_PATH) else {}

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sectors = build_sectors(ctx, news, ts)

    if args.enrich_picks:
        with open(args.enrich_picks, encoding="utf-8") as f:
            picks_data = json.load(f)
        # Accept either a list directly or {risk_adjusted_picks: [...]}
        if isinstance(picks_data, list):
            picks = picks_data
        else:
            picks = picks_data.get("risk_adjusted_picks") or []
        sectors = enrich_with_picks(sectors, picks)

    serialized = json.dumps(sectors, ensure_ascii=False, indent=2)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(serialized)
        n_stocks = len(sectors.get("stocks", {}).get("assets", []))
        n_materials = len(sectors.get("materials", {}).get("assets", []))
        print(f"OK  sectors  → {args.out}  (stocks={n_stocks}, materials={n_materials})")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
