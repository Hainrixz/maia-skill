#!/usr/bin/env python3
"""
Tododeia Pre-fetch Script
==========================
Calculates real technical indicators, valuation metrics, earnings dates,
and insider signals BEFORE LLM agents run.

This eliminates:
- ~60 LLM web searches for RSI/PE/support data (often stale or hallucinated)
- Risk of "response hit the length limit" crashes
- Fake precision (RSI "57" from a 2-week-old article)

Usage:
    python3 tools/pre_fetch.py [TICKER1 TICKER2 ...]
    python3 tools/pre_fetch.py              # uses DEFAULT_TICKERS

Output:
    data/market_context.json
"""

import sys
import os
import json
import contextlib
from datetime import datetime

import urllib.request
import yfinance as yf
import pandas as pd
import numpy as np

# ─── Default watchlist ────────────────────────────────────────────────────────
# Top mega-caps that most commonly appear in Stocks Agent discoveries.
# The agent will use pre-fetched data for these; any newly discovered stock
# outside this list can still do web searches for technicals.
DEFAULT_TICKERS = [
    "NVDA", "AMD", "TSM", "AMZN", "MSFT", "AAPL",
    "GOOGL", "META", "AVGO", "BAC", "JPM", "PLTR",
    "TSLA", "NFLX", "KMI",
]

# Named watchlists — use with: python3 tools/pre_fetch.py --watchlist <name>
# Multiple names allowed: python3 tools/pre_fetch.py --watchlist tech financials
# Individual tickers still work: python3 tools/pre_fetch.py INTC COIN GLD
WATCHLISTS = {
    # Core 15 — same as DEFAULT_TICKERS
    "default": DEFAULT_TICKERS,

    # Extended tech: adds semiconductors, SaaS, and recently discovered high-momentum names
    "tech": [
        "NVDA", "AMD", "TSM", "INTC", "QCOM", "ARM",
        "MSFT", "AAPL", "GOOGL", "META", "AMZN",
        "AVGO", "AMAT", "ASML",
        "PLTR", "SNOW", "CRM", "NOW", "PANW",
        "NFLX", "TSLA",
    ],

    # Financials: banks, payment networks, asset managers
    "financials": [
        "JPM", "BAC", "GS", "MS", "WFC", "C",
        "V", "MA", "PYPL",
        "BLK", "BX",
    ],

    # Materials & energy: precious metals ETFs + oil & gas
    "materials": [
        "GLD", "SLV", "GDX", "GDXJ",
        "XOM", "CVX", "COP", "KMI", "OXY",
        "FCX", "NEM",
    ],

    # Healthcare & biotech
    "healthcare": [
        "LLY", "UNH", "JNJ", "ABBV", "MRK",
        "AMGN", "GILD", "REGN", "MRNA", "PFE",
    ],

    # Indices & macro proxies (use for macro context alongside stocks)
    "macro": [
        "SPY", "QQQ", "IWM", "DIA",
        "TLT", "GLD", "USO", "UUP",
    ],

    # Crypto proxies available on yfinance (spot via -USD suffix)
    "crypto": [
        "BTC-USD", "ETH-USD", "SOL-USD",
        "COIN", "MSTR", "MARA", "RIOT",
    ],

    # Full extended: all of the above deduplicated (~65 tickers, ~3-4 min runtime)
    "all": sorted(set(
        DEFAULT_TICKERS +
        ["INTC", "QCOM", "ARM", "AMAT", "ASML", "SNOW", "CRM", "NOW", "PANW"] +
        ["JPM", "BAC", "GS", "MS", "WFC", "C", "V", "MA", "PYPL", "BLK", "BX"] +
        ["GLD", "SLV", "GDX", "XOM", "CVX", "COP", "OXY", "FCX", "NEM"] +
        ["LLY", "UNH", "JNJ", "ABBV", "MRK", "AMGN", "GILD", "REGN"] +
        ["BTC-USD", "ETH-USD", "SOL-USD", "COIN", "MSTR"]
    )),
}

MACRO_TICKERS = ["^VIX", "^TNX", "^GSPC", "^IRX"]

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(SKILL_ROOT, "data", "market_context.json")


# ─── Technical indicators (pure pandas/numpy — no external deps) ──────────────

def _rsi(closes: pd.Series, window: int = 14) -> float:
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    return round(float(rsi_series.iloc[-1]), 1)


def _macd_signal(closes: pd.Series, slow=26, fast=12, signal=9) -> str:
    exp_fast = closes.ewm(span=fast, adjust=False).mean()
    exp_slow = closes.ewm(span=slow, adjust=False).mean()
    macd = exp_fast - exp_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig

    macd_val = macd.iloc[-1]
    sig_val = sig.iloc[-1]
    hist_now = hist.iloc[-1]
    hist_prev = hist.iloc[-2] if len(hist) > 1 else hist_now

    if macd_val > sig_val:
        return "bullish" if hist_now >= hist_prev else "bullish_weakening"
    else:
        return "bearish" if hist_now <= hist_prev else "bearish_weakening"


def _trend(closes: pd.Series) -> str:
    price = closes.iloc[-1]
    sma50 = closes.rolling(50).mean().iloc[-1]
    sma200 = closes.rolling(200).mean().iloc[-1] if len(closes) >= 200 else None

    if sma200 is not None and not pd.isna(sma200):
        if price > sma50 and price > sma200:
            return "uptrend"
        elif price < sma50 and price < sma200:
            return "downtrend"
        else:
            return "mixed"
    return "uptrend" if price > sma50 else "downtrend"


def _support_resistance(closes: pd.Series):
    price = closes.iloc[-1]
    sma50 = closes.rolling(50).mean().iloc[-1]
    sma200_series = closes.rolling(200).mean()
    sma200 = sma200_series.iloc[-1] if len(closes) >= 200 else None
    low_52w = closes.tail(252).min()
    high_52w = closes.tail(252).max()

    smas_below = [s for s in [sma50, sma200] if s is not None and not pd.isna(s) and s < price]
    support = round(max(smas_below) if smas_below else low_52w, 2)
    resistance = round(high_52w, 2)
    return support, resistance


def _entry_quality(
    rsi: float,
    price: float,
    support: float,
    fcf_margin: float | None = None,
    revenue_growth: float | None = None,
) -> str:
    pct_above = (price - support) / support * 100 if support > 0 else 0
    if rsi < 35:
        # Gate: check if oversold is opportunity or fundamental deterioration
        has_data = fcf_margin is not None or revenue_growth is not None
        if not has_data:
            return "excellent — oversold"
        good_fcf = fcf_margin is None or fcf_margin > 0.10
        not_shrinking = revenue_growth is None or revenue_growth > -0.05
        if good_fcf and not_shrinking:
            return "excellent — oversold"
        elif not good_fcf and revenue_growth is not None and revenue_growth < -0.05:
            return "oversold — fundamentals deteriorating"
        else:
            return "oversold — verify fundamentals"
    elif rsi < 55 and pct_above < 5:
        return "good — near support"
    elif rsi > 70:
        return "poor — overbought"
    elif pct_above > 15:
        return "poor — extended"
    else:
        return "fair"


# ─── Earnings ─────────────────────────────────────────────────────────────────

def _earnings(ticker_obj):
    result = {"next_date": None, "days_away": None, "last_surprise_pct": None, "beat_streak": 0}
    try:
        info = ticker_obj.info
        ts = info.get("earningsTimestamp")
        if ts:
            dt = pd.to_datetime(ts, unit="s")
            result["next_date"] = dt.strftime("%Y-%m-%d")
            result["days_away"] = int((dt - pd.Timestamp.now()).days)
    except Exception:
        pass
    try:
        hist = ticker_obj.get_earnings_history()
        if hist is not None and not hist.empty:
            col = next((c for c in ["surprisePercent", "Surprise(%)"] if c in hist.columns), None)
            if col:
                surprises = hist[col].dropna().head(4).tolist()
                if surprises:
                    result["last_surprise_pct"] = round(float(surprises[0]), 2)
                    result["beat_streak"] = int(sum(1 for s in surprises if s > 0))
    except Exception:
        pass
    return result


# ─── Insider signal ───────────────────────────────────────────────────────────

def _insider(ticker_obj) -> str:
    try:
        txns = ticker_obj.get_insider_transactions()
        if txns is None or txns.empty:
            return "neutral"

        cutoff = pd.Timestamp.now() - pd.Timedelta(days=90)
        date_col = next((c for c in ["Start Date", "startDate", "Date", "date"] if c in txns.columns), None)
        if date_col:
            txns[date_col] = pd.to_datetime(txns[date_col], errors="coerce")
            recent = txns[txns[date_col] >= cutoff]
        else:
            recent = txns

        buys = sells = 0
        for _, row in recent.iterrows():
            text = str(row.get("Transaction", row.get("transaction", ""))).lower()
            if any(k in text for k in ("purchase", "buy", "acquisition")):
                buys += 1
            elif any(k in text for k in ("sale", "sell", "sold")):
                sells += 1

        if buys > sells * 1.5:
            return "bullish"
        elif sells > buys * 1.5:
            return "bearish"
        return "neutral"
    except Exception:
        return "neutral"


# ─── Per-stock fetch ──────────────────────────────────────────────────────────

def fetch_stock(symbol: str) -> dict | None:
    devnull = open(os.devnull, "w")
    try:
        with contextlib.redirect_stderr(devnull):
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y", interval="1d")

        if hist.empty:
            return None

        closes = hist["Close"]
        price = round(float(closes.iloc[-1]), 2)

        rsi = _rsi(closes)
        macd = _macd_signal(closes)
        trend = _trend(closes)
        support, resistance = _support_resistance(closes)
        sma50 = round(float(closes.rolling(50).mean().iloc[-1]), 2)
        sma200_val = closes.rolling(200).mean().iloc[-1]
        sma200 = round(float(sma200_val), 2) if len(closes) >= 200 and not pd.isna(sma200_val) else None

        # Fundamentals from .info (real data from yfinance, not estimated)
        # Computed before entry_quality so it can use them as a quality gate
        try:
            with contextlib.redirect_stderr(devnull):
                info = ticker.info or {}
        except Exception:
            info = {}

        def safe(key):
            v = info.get(key)
            if v in (None, "N/A", float("inf"), float("-inf")):
                return None
            try:
                return round(float(v), 4)
            except (TypeError, ValueError):
                return None

        fcf = safe("freeCashflow")
        revenue = safe("totalRevenue")
        fcf_margin = round(fcf / revenue, 4) if fcf and revenue and revenue > 0 else None
        revenue_growth = safe("revenueGrowth")

        entry = _entry_quality(rsi, price, support, fcf_margin, revenue_growth)

        earnings = _earnings(ticker)
        insider = _insider(ticker)

    except Exception:
        return None
    finally:
        devnull.close()

    return {
        "price": price,
        "technicals": {
            "trend": trend,
            "rsi": rsi,
            "macd": macd,
            "sma_50": sma50,
            "sma_200": sma200,
            "key_support": support,
            "key_resistance": resistance,
            "entry_quality": entry,
        },
        "valuation": {
            "pe": safe("trailingPE"),
            "forward_pe": safe("forwardPE"),
            "peg": safe("pegRatio"),
            "ev_ebitda": safe("enterpriseToEbitda"),
            "price_to_fcf": safe("priceToFreeCashflows"),
        },
        "fundamentals": {
            "revenue_growth_yoy": revenue_growth,
            "gross_margin": safe("grossMargins"),
            "fcf_margin": fcf_margin,
            "debt_equity": safe("debtToEquity"),
            "free_cashflow": fcf,
            "total_revenue": revenue,
        },
        "earnings": earnings,
        "insider_signal": insider,
    }


# ─── Macro fetch ──────────────────────────────────────────────────────────────

def fetch_macro() -> dict:
    devnull = open(os.devnull, "w")
    try:
        with contextlib.redirect_stderr(devnull):
            data = yf.download(
                MACRO_TICKERS, period="6mo", interval="1d", progress=False
            )

        # Handle MultiIndex from yf.download
        if isinstance(data.columns, pd.MultiIndex):
            data = data["Close"]
        elif "Close" in data.columns:
            data = data["Close"]

        latest = data.iloc[-1]
        vix = round(float(latest.get("^VIX", 20)), 2)
        tnx = round(float(latest.get("^TNX", 4.3)), 3)
        irx = round(float(latest.get("^IRX", 3.0)), 3)

        gspc = data["^GSPC"].dropna()
        spy_rsi = _rsi(gspc)

        # Synthetic Fear & Greed (fallback): VIX component + momentum component
        vix_score = max(0.0, min(100.0, 100 - ((vix - 10) / 25 * 100)))
        fg_synthetic = round((vix_score * 0.5) + (spy_rsi * 0.5), 1)

        # Real Fear & Greed from alternative.me (primary source)
        fg = fg_synthetic
        fg_label = (
            "Extreme Fear" if fg < 25 else
            "Fear" if fg < 45 else
            "Neutral" if fg < 55 else
            "Greed" if fg < 75 else
            "Extreme Greed"
        )
        fg_source = "synthetic"
        try:
            req = urllib.request.urlopen(
                "https://api.alternative.me/fng/?limit=1", timeout=5
            )
            fng_data = json.loads(req.read().decode())["data"][0]
            fg = int(fng_data["value"])
            fg_label = fng_data["value_classification"]
            fg_source = "alternative.me"
        except Exception:
            pass  # fallback: keep synthetic values already set above

        tnx_20 = float(data["^TNX"].iloc[-20]) if len(data) >= 20 else tnx
        tnx_trend = "rising" if tnx > tnx_20 * 1.05 else "falling" if tnx < tnx_20 * 0.95 else "stable"

        # Market regime from S&P 500
        sma50 = float(gspc.rolling(50).mean().iloc[-1])
        sma200 = float(gspc.rolling(200).mean().iloc[-1]) if len(gspc) >= 200 else None
        price = float(gspc.iloc[-1])
        if sma200 and price > sma50 > sma200:
            regime = "BULL"
        elif sma200 and price < sma50 < sma200:
            regime = "BEAR"
        else:
            regime = "MIXED"

        return {
            "vix": vix,
            "yield_10y": tnx,
            "yield_3m": irx,
            "yield_spread_10y_3m": round(tnx - irx, 3),
            "spy_rsi": spy_rsi,
            "fear_greed_index": fg,
            "fear_greed_label": fg_label,
            "fear_greed_synthetic": fg_synthetic,
            "fear_greed_source": fg_source,
            "yield_trend": tnx_trend,
            "market_regime": regime,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        devnull.close()


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    # --watchlist NAME [NAME2 ...] — select one or more named watchlists
    # Everything else is treated as individual ticker symbols
    if "--watchlist" in args:
        idx = args.index("--watchlist")
        watchlist_names = []
        individual = []
        after = args[idx + 1:]
        for token in after:
            if token in WATCHLISTS:
                watchlist_names.append(token)
            elif not token.startswith("--"):
                # Unknown name — treat as individual ticker
                individual.append(token.upper())
            else:
                break
        before = [t.upper() for t in args[:idx] if not t.startswith("--")]

        tickers_set = list(dict.fromkeys(
            before +
            [t for name in watchlist_names for t in WATCHLISTS[name]] +
            individual
        ))
        if not tickers_set:
            print(f"[pre_fetch] Unknown watchlist(s). Available: {', '.join(WATCHLISTS)}")
            sys.exit(1)
        tickers = tickers_set
        label = f"watchlist={'+'.join(watchlist_names) or 'none'}"
    elif args:
        tickers = [t.upper() for t in args]
        label = "custom"
    else:
        tickers = DEFAULT_TICKERS
        label = "default"

    print(f"[pre_fetch] {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')} — {label} — fetching {len(tickers)} tickers + macro")

    stocks = {}
    for symbol in tickers:
        print(f"  {symbol:<6}", end=" ", flush=True)
        result = fetch_stock(symbol)
        if result:
            t = result["technicals"]
            v = result["valuation"]
            print(f"RSI={t['rsi']}  {t['trend']:<10}  PEG={v['peg']}  entry={t['entry_quality']}")
            stocks[symbol] = result
        else:
            print("SKIP — no data")

    print("[pre_fetch] Fetching macro...", end=" ", flush=True)
    macro = fetch_macro()
    if "error" in macro:
        print(f"ERROR: {macro['error']}")
    else:
        fg_src = macro.get('fear_greed_source', 'synthetic')
        fg_synth = f"  synthetic={macro.get('fear_greed_synthetic', '?')}" if fg_src == 'alternative.me' else ''
        print(f"VIX={macro['vix']}  F&G={macro['fear_greed_index']} ({macro['fear_greed_label']}) [{fg_src}]{fg_synth}  regime={macro['market_regime']}")

    output = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tickers_fetched": list(stocks.keys()),
        "stocks": stocks,
        "macro": macro,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"[pre_fetch] ✓ Written → {OUTPUT_PATH}  ({os.path.getsize(OUTPUT_PATH):,} bytes)")


if __name__ == "__main__":
    main()
