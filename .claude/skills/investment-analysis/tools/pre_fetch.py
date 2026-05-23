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
import glob
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import urllib.request
import yfinance as yf
import pandas as pd
import numpy as np

# ─── Watchlists ───────────────────────────────────────────────────────────────
# DEFAULT_TICKERS is the full "all" watchlist — pre_fetch covers the entire
# universe by default so the Stocks Agent always has a pre-screened candidate
# list and never needs web searches for technicals.
# Run with individual tickers or --watchlist <name> to narrow the scope.

_CORE = [
    "NVDA", "AMD", "TSM", "AMZN", "MSFT", "AAPL",
    "GOOGL", "META", "AVGO", "BAC", "JPM", "PLTR",
    "TSLA", "NFLX", "KMI",
]

# Named watchlists — use with: python3 tools/pre_fetch.py --watchlist <name>
# Multiple names allowed: python3 tools/pre_fetch.py --watchlist tech financials
# Individual tickers still work: python3 tools/pre_fetch.py INTC COIN GLD
WATCHLISTS = {
    # Core 15
    "default": _CORE,

    # Extended tech: adds semiconductors, SaaS, and recently discovered high-momentum names
    "tech": [
        "NVDA", "AMD", "TSM", "INTC", "QCOM", "ARM",
        "MSFT", "AAPL", "GOOGL", "META", "AMZN", "IBM",
        "AVGO", "AMAT", "ASML", "ASLM",
        "PLTR", "SNOW", "CRM", "NOW", "PANW",
        "NFLX", "TSLA", "RIVN", "SONY",
    ],

    # Financials: banks, payment networks, asset managers, fintech
    "financials": [
        "JPM", "BAC", "GS", "MS", "WFC", "C",
        "V", "MA", "PYPL",
        "BLK", "BX",
        "NU", "SOFI",
    ],

    # Consumer: entertainment, retail, restaurants, global ecommerce
    "consumer": [
        "DIS", "NFLX",
        "HD", "SBUX",
        "BABA", "MELI",
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

    # Crypto proxies — removed (no longer tracked)
    # "crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "COIN", "MSTR", "MARA", "RIOT"],

    # Full extended: all of the above deduplicated (~65 tickers, ~3-4 min runtime)
    "all": sorted(set(
        _CORE +
        ["INTC", "QCOM", "ARM", "AMAT", "ASML", "ASLM", "SNOW", "CRM", "NOW", "PANW"] +
        ["JPM", "BAC", "GS", "MS", "WFC", "C", "V", "MA", "PYPL", "BLK", "BX"] +
        ["GLD", "SLV", "GDX", "XOM", "CVX", "COP", "OXY", "FCX", "NEM"] +
        ["LLY", "UNH", "JNJ", "ABBV", "MRK", "AMGN", "GILD", "REGN"] +
        # New additions (May 2026)
        ["SONY", "BABA", "RIVN", "MELI", "NU", "SOFI", "DIS", "HD", "SBUX", "IBM"]
    )),
}

# Default: full universe so the Stocks Agent always has a pre-screened list
DEFAULT_TICKERS = WATCHLISTS["all"]

MACRO_TICKERS = ["^VIX", "^TNX", "^GSPC", "^IRX"]

# ─── Correlation groups ───────────────────────────────────────────────────────
# Assets within the same group tend to move together (high beta correlation).
# Used to detect over-concentration in picks and generate warnings.
# Rule enforced downstream: max MAX_PICKS_PER_GROUP picks per group.
#
# Design notes:
# - A ticker can belong to only ONE group (primary driver wins).
# - "precious_metals" covers GLD+SLV+GDX+NEM — all gold/silver proxies.
# - "semiconductors" is separate from "big_tech" because chip cycles diverge.
# - FCX is "base_metals" not "precious_metals" (copper-driven, not gold).
# - COIN/MSTR are "crypto_equity" — they track crypto but add equity risk.

CORRELATION_GROUPS: dict[str, list[str]] = {
    "precious_metals":       ["GLD", "SLV", "GDX", "NEM"],
    "semiconductors":        ["NVDA", "AMD", "INTC", "QCOM", "TSM", "ARM", "AMAT", "ASML", "AVGO"],
    "big_tech":              ["MSFT", "AAPL", "GOOGL", "META", "AMZN", "IBM", "PLTR", "SONY"],
    "financials":            ["JPM", "BAC", "GS", "MS", "WFC", "C"],
    "payments":              ["V", "MA", "PYPL"],
    "healthcare":            ["JNJ", "ABBV", "MRK", "AMGN", "GILD", "REGN", "LLY", "UNH"],
    "energy":                ["XOM", "CVX", "COP", "OXY", "KMI"],
    "base_metals":           ["FCX"],
    "saas":                  ["CRM", "NOW", "SNOW", "PANW"],
    "asset_managers":        ["BLK", "BX"],
    # New groups added May 2026
    "ev":                    ["TSLA", "RIVN"],
    "streaming":             ["NFLX", "DIS"],
    "ecommerce_global":      ["BABA", "MELI"],
    "fintech":               ["NU", "SOFI"],
    "consumer_discretionary": ["HD", "SBUX"],
}

# Reverse lookup: symbol → group name (built once at import time)
_SYMBOL_TO_GROUP: dict[str, str] = {
    sym: group
    for group, symbols in CORRELATION_GROUPS.items()
    for sym in symbols
}

# Maximum picks allowed per correlation group in a single report.
# Enforced as a warning (not a hard cut) so the MegaAgent has final judgment.
MAX_PICKS_PER_GROUP = 2

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(SKILL_ROOT, "data", "market_context.json")

# Fundamentals cache: balance-sheet, income-stmt, cashflow, earnings history,
# and insider transactions are expensive yfinance calls that change quarterly.
# FUND_CACHE_TTL_DAYS = how many days before a cache entry is considered stale.
# Set to 0 to disable caching (forces full re-fetch every run).
CACHE_DIR = os.path.join(SKILL_ROOT, "data", "cache", "fundamentals")
FUND_CACHE_TTL_DAYS = 5


# ─── Fundamentals cache helpers ───────────────────────────────────────────────

def _load_fund_cache(symbol: str) -> dict | None:
    """Load cached heavy fundamentals for symbol.

    Returns the cached dict if it exists and is not older than
    FUND_CACHE_TTL_DAYS. Returns None on cache miss, expiry, or read error.
    """
    if FUND_CACHE_TTL_DAYS <= 0:
        return None
    path = os.path.join(CACHE_DIR, f"{symbol}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            cached = json.load(f)
        fetched_str = cached.get("fetched_at", "2000-01-01T00:00:00Z")
        fetched = datetime.strptime(fetched_str, "%Y-%m-%dT%H:%M:%SZ")
        age_days = (datetime.utcnow() - fetched).total_seconds() / 86400
        if age_days > FUND_CACHE_TTL_DAYS:
            return None
        return cached
    except Exception:
        return None


def _save_fund_cache(symbol: str, data: dict) -> None:
    """Persist heavy fundamentals to the per-symbol cache file."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        data["fetched_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        path = os.path.join(CACHE_DIR, f"{symbol}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception:
        pass  # cache write failure is non-fatal


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


def _atr(hist: pd.DataFrame, window: int = 14) -> float | None:
    """Average True Range over `window` days."""
    try:
        high = hist["High"]
        low  = hist["Low"]
        close_prev = hist["Close"].shift(1)
        tr = pd.concat([
            high - low,
            (high - close_prev).abs(),
            (low  - close_prev).abs(),
        ], axis=1).max(axis=1)
        return round(float(tr.rolling(window).mean().iloc[-1]), 4)
    except Exception:
        return None


def _financial_health(ticker_obj) -> dict:
    """Compute Altman Z-Score and Piotroski F-Score from yfinance statements.

    Returns a dict with keys: altman_z, altman_zone, piotroski, piotroski_strength.
    Returns null values when data is insufficient (ETFs, financials, no statements).

    Altman Z (non-financial companies, Altman 1968):
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        X1 = working_capital / total_assets
        X2 = retained_earnings / total_assets
        X3 = EBIT / total_assets
        X4 = market_cap / total_liabilities
        X5 = revenue / total_assets
        Zones: > 2.99 = safe, 1.81-2.99 = gray, < 1.81 = distress

    Piotroski F-Score (0-9 binary checks):
        Profitability (4): ROA>0, CFO>0, delta_ROA>0, CFO>NI (accruals)
        Leverage (3): delta_LTD<0, delta_CR>0, no share dilution
        Efficiency (2): delta_gross_margin>0, delta_asset_turnover>0
    """
    null_result = {
        "altman_z": None, "altman_zone": "N/A",
        "piotroski": None, "piotroski_strength": "N/A",
    }
    try:
        info = ticker_obj.info or {}
        quote_type = info.get("quoteType", "")
        # Skip ETFs, funds, and indices — no meaningful balance sheet
        if quote_type in ("ETF", "MUTUALFUND", "INDEX", "FUTURE", "CURRENCY"):
            return null_result

        bs  = ticker_obj.get_balance_sheet()
        inc = ticker_obj.get_income_stmt()
        cf  = ticker_obj.get_cash_flow()

        if bs is None or inc is None or bs.empty or inc.empty:
            return null_result

        def g(df, *keys, col=0):
            """Safely get a value from a statement DataFrame (rows=items, cols=periods)."""
            for key in keys:
                # Case-insensitive row match
                matches = [i for i in df.index if str(i).lower() == key.lower()]
                if matches:
                    val = df.loc[matches[0]].iloc[col]
                    try:
                        v = float(val)
                        return v if not (pd.isna(v) or v in (float('inf'), float('-inf'))) else None
                    except (TypeError, ValueError):
                        return None
            return None

        # ── Altman Z-Score inputs ───────────────────────────────────────────
        total_assets  = g(bs, "TotalAssets", "Total Assets")
        total_liab    = g(bs, "TotalLiabilitiesNetMinorityInterest", "Total Liabilities",
                          "TotalLiabilities", "TotalLiabilitiesNetMinority")
        current_assets = g(bs, "CurrentAssets", "Total Current Assets")
        current_liab   = g(bs, "CurrentLiabilities", "Total Current Liabilities")
        retained_earn  = g(bs, "RetainedEarnings", "Retained Earnings")
        ebit           = g(inc, "EBIT", "Ebit", "OperatingIncome", "Operating Income")
        revenue        = g(inc, "TotalRevenue", "Total Revenue", "Revenue")
        market_cap     = float(info.get("marketCap") or 0) or None

        # Skip financials (banks/insurance) — Altman Z not applicable
        sector = info.get("sector", "")
        is_financial = sector in ("Financial Services", "Finance")

        altman_z = None
        altman_zone = "N/A"
        if not is_financial and all(v is not None and v != 0 for v in [total_assets, total_liab, market_cap, revenue, ebit]):
            wc = (current_assets or 0) - (current_liab or 0)
            X1 = wc / total_assets
            X2 = (retained_earn or 0) / total_assets
            X3 = ebit / total_assets
            X4 = market_cap / total_liab
            X5 = revenue / total_assets
            z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
            altman_z = round(z, 2)
            altman_zone = "safe" if z > 2.99 else "gray" if z > 1.81 else "distress"
        elif is_financial:
            altman_zone = "N/A (financial)"

        # ── Piotroski F-Score ───────────────────────────────────────────────
        piotroski = None
        piotroski_strength = "N/A"
        try:
            bs1 = ticker_obj.get_balance_sheet()   # most recent period
            inc1 = ticker_obj.get_income_stmt()
            cf1  = ticker_obj.get_cash_flow()

            if bs1 is not None and not bs1.empty and bs1.shape[1] >= 2:
                # Helpers for period 0 (current) and period 1 (prior year)
                def g0(df, *k): return g(df, *k, col=0)
                def g1(df, *k): return g(df, *k, col=1)

                ta0 = g0(bs1, "TotalAssets", "Total Assets")
                ta1 = g1(bs1, "TotalAssets", "Total Assets")
                if not ta0 or not ta1 or ta0 == 0 or ta1 == 0:
                    raise ValueError("Missing total assets")

                ni0   = g0(inc1, "NetIncome", "Net Income")
                roa0  = (ni0 / ta0) if ni0 is not None else None
                ni1   = g1(inc1, "NetIncome", "Net Income")
                roa1  = (ni1 / ta1) if ni1 is not None else None

                cfo0  = g0(cf1,  "OperatingCashFlow", "Operating Cash Flow",
                           "CashFlowFromOperations", "NetCashFromOperatingActivities")

                ltd0  = g0(bs1, "LongTermDebt", "Long Term Debt")
                ltd1  = g1(bs1, "LongTermDebt", "Long Term Debt")

                ca0   = g0(bs1, "CurrentAssets", "Total Current Assets")
                cl0   = g0(bs1, "CurrentLiabilities", "Total Current Liabilities")
                ca1   = g1(bs1, "CurrentAssets", "Total Current Assets")
                cl1   = g1(bs1, "CurrentLiabilities", "Total Current Liabilities")
                cr0   = (ca0 / cl0) if (ca0 and cl0 and cl0 != 0) else None
                cr1   = (ca1 / cl1) if (ca1 and cl1 and cl1 != 0) else None

                shares0 = g0(bs1, "OrdinarySharesNumber", "CommonStock", "SharesOutstanding")
                shares1 = g1(bs1, "OrdinarySharesNumber", "CommonStock", "SharesOutstanding")

                rev0  = g0(inc1, "TotalRevenue", "Total Revenue", "Revenue")
                rev1  = g1(inc1, "TotalRevenue", "Total Revenue", "Revenue")
                gp0   = g0(inc1, "GrossProfit", "Gross Profit")
                gp1   = g1(inc1, "GrossProfit", "Gross Profit")
                gm0   = (gp0 / rev0) if (gp0 and rev0 and rev0 != 0) else None
                gm1   = (gp1 / rev1) if (gp1 and rev1 and rev1 != 0) else None
                at0   = (rev0 / ta0) if (rev0 and ta0 != 0) else None
                at1   = (rev1 / ta1) if (rev1 and ta1 != 0) else None

                checks = [
                    # Profitability
                    int(roa0 is not None and roa0 > 0),                           # F1: ROA > 0
                    int(cfo0 is not None and cfo0 > 0),                           # F2: CFO > 0
                    int(roa0 is not None and roa1 is not None and roa0 > roa1),   # F3: delta ROA > 0
                    int(cfo0 is not None and ni0 is not None and cfo0 > ni0),     # F4: CFO > NI (accruals)
                    # Leverage
                    int(ltd0 is not None and ltd1 is not None and ltd0 < ltd1),   # F5: LTD decreased
                    int(cr0 is not None and cr1 is not None and cr0 > cr1),       # F6: CR improved
                    int(shares0 is not None and shares1 is not None and shares0 <= shares1),  # F7: no dilution
                    # Efficiency
                    int(gm0 is not None and gm1 is not None and gm0 > gm1),      # F8: GM improved
                    int(at0 is not None and at1 is not None and at0 > at1),      # F9: asset turnover up
                ]
                piotroski = sum(checks)
                piotroski_strength = (
                    "strong" if piotroski >= 7 else
                    "weak"   if piotroski <= 2 else
                    "neutral"
                )
        except Exception:
            pass

        return {
            "altman_z": altman_z,
            "altman_zone": altman_zone,
            "piotroski": piotroski,
            "piotroski_strength": piotroski_strength,
        }
    except Exception:
        return null_result


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

def _earnings_next(info: dict) -> dict:
    """Extract next earnings date from a pre-fetched info dict (no extra API call)."""
    result = {"next_date": None, "days_away": None,
              "last_surprise_pct": None, "beat_streak": 0}
    try:
        ts = info.get("earningsTimestamp")
        if ts:
            dt = pd.to_datetime(ts, unit="s")
            result["next_date"] = dt.strftime("%Y-%m-%d")
            result["days_away"] = int((dt - pd.Timestamp.now()).days)
    except Exception:
        pass
    return result


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


# ─── Split detection ────────────────────────────────────────────────────────

def _detect_recent_split(ticker_obj, days: int = 60) -> dict | None:
    """Return split info if a stock split occurred in the last `days` days.

    yfinance .actions returns a DataFrame with columns [Dividends, Stock Splits].
    A split ratio of 12.0 means a 12:1 forward split — the share count increases
    and historic prices are retroactively adjusted, invalidating entry_price
    comparisons across the split date.

    Returns None if no recent split or if data is unavailable.
    """
    try:
        actions = ticker_obj.actions
        if actions is None or actions.empty:
            return None
        if "Stock Splits" not in actions.columns:
            return None
        splits = actions[actions["Stock Splits"] > 0]["Stock Splits"]
        if splits.empty:
            return None
        # Normalise index timezone for comparison
        idx = splits.index
        if idx.tz is None:
            idx = idx.tz_localize("UTC")
        cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days)
        recent = splits[idx >= cutoff]
        if recent.empty:
            return None
        ratio = float(recent.iloc[-1])
        split_date = recent.index[-1].strftime("%Y-%m-%d")
        ratio_str = f"{int(ratio)}:1" if ratio == int(ratio) else f"{ratio}:1"
        return {"split_date": split_date, "ratio": ratio_str}
    except Exception:
        return None


# ─── Per-stock fetch ──────────────────────────────────────────────────────────

def fetch_stock(symbol: str) -> dict | None:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1y", interval="1d")

        if hist.empty:
            return None

        closes = hist["Close"]
        price = round(float(closes.iloc[-1]), 2)

        # ── Split detection (early exit — stale prices invalidate comparisons) ──
        split_info = _detect_recent_split(ticker)
        if split_info:
            return {
                "price": price,
                "split_detected": True,
                "split_info": split_info,
                "technicals": {
                    "rsi": 50, "trend": "mixed", "macd": "neutral",
                    "sma_50": price, "sma_200": None,
                    "key_support": 0, "key_resistance": price,
                    "entry_quality": "split_detected",
                    "volume_ratio": None, "range_52w_pct": None,
                },
                "valuation": {}, "fundamentals": {},
                "earnings": {"next_date": None, "days_away": None,
                              "last_surprise_pct": None, "beat_streak": 0},
                "insider_signal": "neutral",
                "short_interest": {"short_ratio": None, "short_float_pct": None},
                "atr_14": None,
                "financial_health": {
                    "altman_z": None, "altman_zone": "N/A",
                    "piotroski": None, "piotroski_strength": "N/A",
                },
            }

        rsi = _rsi(closes)
        macd = _macd_signal(closes)
        trend = _trend(closes)
        support, resistance = _support_resistance(closes)
        sma50 = round(float(closes.rolling(50).mean().iloc[-1]), 2)
        sma200_val = closes.rolling(200).mean().iloc[-1]
        sma200 = round(float(sma200_val), 2) if len(closes) >= 200 and not pd.isna(sma200_val) else None

        # Volume anomaly: ratio of latest session volume vs 30-day average.
        # >1.5 = above-average activity; >2.0 = high conviction move.
        volumes = hist["Volume"]
        vol_30d_avg = float(volumes.rolling(30).mean().iloc[-1])
        volume_ratio = round(float(volumes.iloc[-1]) / vol_30d_avg, 2) if vol_30d_avg > 0 else None

        # 52-week range position: 0% = at 52w low, 100% = at 52w high.
        # Stocks below 15% of range near multi-year support; above 85% = extended.
        low_52w = float(closes.tail(252).min())
        high_52w = float(closes.tail(252).max())
        range_52w_pct = round((price - low_52w) / (high_52w - low_52w) * 100, 1) if high_52w > low_52w else None

        # Fundamentals from .info (real data from yfinance, not estimated)
        # Computed before entry_quality so it can use them as a quality gate
        try:
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

        # Short interest — days to cover (short_ratio) and % of float shorted.
        # short_ratio > 10 = highly shorted (squeeze candidate if oversold).
        # short_float_pct > 20% = crowded short (potential squeeze fuel).
        short_ratio = safe("shortRatio")
        short_float = safe("shortPercentOfFloat")
        short_float_pct = round(short_float * 100, 2) if short_float is not None else None

        entry = _entry_quality(rsi, price, support, fcf_margin, revenue_growth)

        atr_14 = _atr(hist)

        # Earnings next_date/days_away: always fresh from the info dict already fetched.
        earnings = _earnings_next(info)

        # ── Cache-backed heavy computations ──────────────────────────────────
        # These three yfinance calls (get_balance_sheet, get_income_stmt,
        # get_cash_flow, get_earnings_history, get_insider_transactions) are
        # expensive and return data that changes at most quarterly.
        # On a cache hit we skip all five calls — ~60% runtime reduction for
        # warm runs (same-day or same-week repeated executions).
        cached_fund = _load_fund_cache(symbol)
        if cached_fund is not None:
            financial_health = cached_fund["financial_health"]
            earnings["beat_streak"]       = cached_fund.get("beat_streak", 0)
            earnings["last_surprise_pct"] = cached_fund.get("last_surprise_pct")
            insider                        = cached_fund.get("insider_signal", "neutral")
        else:
            financial_health   = _financial_health(ticker)
            earnings_hist      = _earnings(ticker)         # full call incl. history
            earnings["beat_streak"]       = earnings_hist.get("beat_streak", 0)
            earnings["last_surprise_pct"] = earnings_hist.get("last_surprise_pct")
            insider = _insider(ticker)
            _save_fund_cache(symbol, {
                "symbol":           symbol,
                "financial_health": financial_health,
                "beat_streak":      earnings["beat_streak"],
                "last_surprise_pct": earnings["last_surprise_pct"],
                "insider_signal":   insider,
            })

    except Exception:
        return None

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
            "volume_ratio": volume_ratio,
            "range_52w_pct": range_52w_pct,
        },
        "valuation": {
            "pe": safe("trailingPE"),
            "forward_pe": safe("forwardPE"),
            "peg": safe("trailingPegRatio") or safe("pegRatio"),
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
        "short_interest": {
            "short_ratio": short_ratio,
            "short_float_pct": short_float_pct,
        },
        "atr_14": atr_14,
        "financial_health": financial_health,
    }


# ─── Macro fetch ──────────────────────────────────────────────────────────────

def fetch_macro() -> dict:
    try:
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
            "spy_price": round(float(gspc.iloc[-1]), 2),
            "spy_rsi": spy_rsi,
            "fear_greed_value": fg,
            "fear_greed_index": fg,
            "fear_greed_label": fg_label,
            "fear_greed_synthetic": fg_synthetic,
            "fear_greed_source": fg_source,
            "yield_trend": tnx_trend,
            "market_regime": regime,
        }
    except Exception as e:
        return {"error": str(e)}


# ─── Composite scoring ───────────────────────────────────────────────────────

def _composite_score(c: dict) -> float:
    """Return a 0–100 composite ranking score for a pre-screened candidate.

    Replaces the old (entry_quality_rank, rsi) two-key sort with a weighted
    multi-factor signal that incorporates fundamental quality alongside
    technical timing.

    Weights:
        RSI proximity to oversold  30%  — primary entry-timing signal
        Piotroski F-Score          20%  — fundamental quality (0–9)
        Altman Z zone              15%  — bankruptcy risk
        Insider signal             15%  — insider conviction
        Earnings beat streak       10%  — execution consistency (0–4 quarters)
        Volume ratio               10%  — move confirmation

    All components are normalised to [0, 1] before weighting.
    N/A values (ETFs, financials) default to 0.5 (neutral — no penalty/bonus).
    Higher score = better candidate.
    """
    rsi = float(c.get("rsi") or 50)
    # RSI: best signal near 20-30, worst above 65.  (65-rsi)/65 → [0,1]
    rsi_score = max(0.0, (65.0 - rsi) / 65.0)

    piof = c.get("piotroski")
    piof_score = (float(piof) / 9.0) if piof is not None else 0.5

    zone = (c.get("altman_zone") or "").lower()
    altman_score = 1.0 if "safe" in zone else 0.0 if "distress" in zone else 0.5

    insider = (c.get("insider_signal") or "neutral").lower()
    insider_score = {"bullish": 1.0, "neutral": 0.5, "bearish": 0.0}.get(insider, 0.5)

    beat = int(c.get("beat_streak") or 0)
    beat_score = min(beat, 4) / 4.0

    vol = float(c.get("volume_ratio") or 1.0)
    vol_score = min(max(vol, 0.0) / 3.0, 1.0)

    return round((
        0.30 * rsi_score    +
        0.20 * piof_score   +
        0.15 * altman_score +
        0.15 * insider_score+
        0.10 * beat_score   +
        0.10 * vol_score
    ) * 100, 1)


# ─── Candidate filter ───────────────────────────────────────────────────────

def filter_candidates(stocks: dict, top_n: int = 35) -> list[dict]:
    """Return the top_n actionable candidates from a pre-fetched universe.

    Exclusion rules (hard gates — no LLM judgment needed):
    - RSI > 70           → overbought, skip
    - entry_quality starts with "poor" → bad entry, skip

    Ranking for the survivors:
    1. entry_quality order: excellent < good < fair (lower index = better)
    2. Within same quality tier: sort by RSI ascending (more oversold = first)

    The returned list is injected directly into the Stocks Agent prompt as
    SCREENED_CANDIDATES, replacing the open-ended web discovery step.
    """
    QUALITY_RANK = {
        "excellent — oversold": 0,    # oversold + healthy fundamentals
        "oversold — verify":    1,    # oversold, fundamentals unclear
        "good":                 2,    # near support, RSI ok
        "fair":                 3,    # no clear edge
        "oversold — fundamentals": 4, # oversold but deteriorating — ranked last
        "oversold":             4,    # generic fallback
    }

    candidates = []
    for symbol, data in stocks.items():
        tech = data.get("technicals", {})
        rsi = tech.get("rsi", 100)
        entry = tech.get("entry_quality", "")

        if rsi > 70:
            continue
        if entry.startswith("poor"):
            continue
        if data.get("split_detected"):
            continue

        quality_key = next((k for k in QUALITY_RANK if entry.startswith(k)), "fair")
        candidates.append({
            "symbol": symbol,
            "price": data.get("price"),
            # price_at_fetch is the immutable baseline for accuracy tracking.
            # MegaAgent must use this value (not a web-searched price) when
            # comparing next-run prices against the entry to compute accuracy.
            "price_at_fetch": data.get("price"),
            "rsi": rsi,
            "trend": tech.get("trend"),
            "entry_quality": entry,
            # correlation_group: the asset family this ticker belongs to.
            # Used downstream to detect over-concentration in picks.
            "correlation_group": _SYMBOL_TO_GROUP.get(symbol, "other"),
            "forward_pe": data.get("valuation", {}).get("forward_pe"),
            "peg": data.get("valuation", {}).get("peg"),
            "revenue_growth_yoy": data.get("fundamentals", {}).get("revenue_growth_yoy"),
            "fcf_margin": data.get("fundamentals", {}).get("fcf_margin"),
            "earnings_days_away": data.get("earnings", {}).get("days_away"),
            "beat_streak": data.get("earnings", {}).get("beat_streak"),
            "insider_signal": data.get("insider_signal"),
            "volume_ratio": data.get("technicals", {}).get("volume_ratio"),
            "range_52w_pct": data.get("technicals", {}).get("range_52w_pct"),
            "short_ratio": data.get("short_interest", {}).get("short_ratio"),
            "short_float_pct": data.get("short_interest", {}).get("short_float_pct"),
            "atr_14": data.get("atr_14"),
            "altman_z": data.get("financial_health", {}).get("altman_z"),
            "altman_zone": data.get("financial_health", {}).get("altman_zone"),
            "piotroski": data.get("financial_health", {}).get("piotroski"),
            "piotroski_strength": data.get("financial_health", {}).get("piotroski_strength"),
            "_sort_key": (QUALITY_RANK.get(quality_key, 2), rsi),
        })

    # Compute composite score for every survivor, then sort descending.
    # _sort_key (quality+RSI) is kept as a tiebreaker reference but not used
    # for the final sort — composite_score replaces it.
    for c in candidates:
        c["composite_score"] = _composite_score(c)
        del c["_sort_key"]

    candidates.sort(key=lambda x: -x["composite_score"])

    return candidates[:top_n]


# ─── Correlation warnings ──────────────────────────────────────────────────────

def build_correlation_warnings(candidates: list[dict]) -> list[dict]:
    """Detect over-concentration in the screened candidate list.

    Returns a list of warning dicts, one per group that exceeds
    MAX_PICKS_PER_GROUP candidates. Each warning includes the group name,
    the tickers involved, and a suggested action for the MegaAgent.

    These warnings are injected into market_context.json as
    `correlation_warnings` and MUST be passed to the MegaAgent so it can
    enforce the max-picks-per-group rule when building the final portfolio.
    """
    from collections import defaultdict

    group_members: dict[str, list[str]] = defaultdict(list)
    for c in candidates:
        group = c.get("correlation_group", "other")
        group_members[group].append(c["symbol"])

    warnings_out = []
    for group, symbols in group_members.items():
        if len(symbols) > MAX_PICKS_PER_GROUP:
            # Rank by RSI ascending (most oversold = best pick to keep)
            ranked = sorted(
                [c for c in candidates if c.get("correlation_group") == group],
                key=lambda x: x["rsi"],
            )
            keep = [r["symbol"] for r in ranked[:MAX_PICKS_PER_GROUP]]
            cut  = [r["symbol"] for r in ranked[MAX_PICKS_PER_GROUP:]]
            warnings_out.append({
                "group": group,
                "count": len(symbols),
                "max_allowed": MAX_PICKS_PER_GROUP,
                "all_candidates": symbols,
                "suggested_keep": keep,
                "suggested_cut": cut,
                "message": (
                    f"Over-concentration: {len(symbols)} '{group}' candidates "
                    f"({', '.join(symbols)}). "
                    f"Recommend keeping max {MAX_PICKS_PER_GROUP}: {', '.join(keep)}. "
                    f"Consider cutting: {', '.join(cut)}."
                ),
            })

    return warnings_out


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

    print(f"[pre_fetch] {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')} — {label} — fetching {len(tickers)} tickers + macro (parallel)")

    stocks = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_stock, symbol): symbol for symbol in tickers}
        for future in as_completed(futures):
            symbol = futures[future]
            result = future.result()
            if result and result.get("split_detected"):
                si = result["split_info"]
                print(f"  {symbol:<6} SPLIT — {si['ratio']} on {si['split_date']} — excluded from candidates")
                stocks[symbol] = result  # kept in prices_snapshot, excluded from candidates
            elif result:
                t = result["technicals"]
                v = result["valuation"]
                print(f"  {symbol:<6} RSI={t['rsi']}  {t['trend']:<10}  PEG={v['peg']}  entry={t['entry_quality']}")
                stocks[symbol] = result
            else:
                print(f"  {symbol:<6} SKIP — no data")

    print("[pre_fetch] Fetching macro...", end=" ", flush=True)
    macro = fetch_macro()
    if "error" in macro:
        print(f"ERROR: {macro['error']}")
    else:
        fg_src = macro.get('fear_greed_source', 'synthetic')
        fg_synth = f"  synthetic={macro.get('fear_greed_synthetic', '?')}" if fg_src == 'alternative.me' else ''
        print(f"VIX={macro['vix']}  F&G={macro['fear_greed_index']} ({macro['fear_greed_label']}) [{fg_src}]{fg_synth}  regime={macro['market_regime']}")

    candidates = filter_candidates(stocks)
    print(f"[pre_fetch] Screened candidates: {len(candidates)}/{len(stocks)} pass RSI+entry filter")
    for c in candidates:
        score = c.get('composite_score', 0)
        cache_tag = "[C]" if _load_fund_cache(c['symbol']) else "   "
        print(f"  {cache_tag} {c['symbol']:<6}  RSI={c['rsi']}  score={score:>5.1f}  {c['entry_quality']}")

    correlation_warnings = build_correlation_warnings(candidates)
    if correlation_warnings:
        print(f"[pre_fetch] ⚠ Correlation warnings ({len(correlation_warnings)}):")
        for w in correlation_warnings:
            print(f"  {w['message']}")
    else:
        print("[pre_fetch] ✓ No correlation over-concentration detected")

    fetch_ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # prices_snapshot: immutable price record for ALL fetched tickers at this
    # exact moment. Used by the next run to compute real accuracy: compare
    # previous run's pick entry_price against prices_snapshot[symbol].price.
    # Never re-fetched or reconstructed — ground truth only.
    prices_snapshot = {
        symbol: {
            "price": data["price"],
            "fetched_at": fetch_ts,
        }
        for symbol, data in stocks.items()
    }

    output = {
        "generated_at": fetch_ts,
        "tickers_fetched": list(stocks.keys()),
        "prices_snapshot": prices_snapshot,
        "candidates": candidates,
        "correlation_warnings": correlation_warnings,
        "stocks": stocks,
        "macro": macro,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"[pre_fetch] ✓ Written → {OUTPUT_PATH}  ({os.path.getsize(OUTPUT_PATH):,} bytes)")

    # Retain only the last 30 history files to prevent unbounded growth
    history_dir = os.path.join(SKILL_ROOT, "output", "history")
    if os.path.isdir(history_dir):
        history_files = sorted(glob.glob(os.path.join(history_dir, "*.json")))
        for old_file in history_files[:-30]:
            os.remove(old_file)
            print(f"[pre_fetch] Pruned old history: {os.path.basename(old_file)}")


if __name__ == "__main__":
    main()
