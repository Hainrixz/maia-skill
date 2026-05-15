#!/usr/bin/env python3
"""
portfolio_fetch.py — Fetches fresh market data + news for portfolio positions only.

Reads data/portfolio.json, fetches RSI/price/fundamentals via yfinance,
and writes data/portfolio_market.json for the MegaAgent prompt.

Usage:
    python3 tools/portfolio_fetch.py

Output:
    data/portfolio_market.json
"""

import json
import warnings
import logging
import sys
import os
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

import yfinance as yf
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "data")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "portfolio_market.json")

# ---------------------------------------------------------------------------
# RSI helper
# ---------------------------------------------------------------------------
def calc_rsi(closes: pd.Series, period: int = 14) -> float:
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    return round(float(rsi.iloc[-1]), 1) if not rsi.empty else None

# ---------------------------------------------------------------------------
# News helpers (same keyword approach as news_fetch.py)
# ---------------------------------------------------------------------------
_POSITIVE_KW = [
    "beat", "beats", "exceeds", "record", "growth", "breakthrough", "surge",
    "upgrade", "upgraded", "raises", "raised", "buyback", "dividend",
    "expansion", "partnership", "approval", "approved", "outperform",
    "strong", "rally", "profit", "milestone", "award", "innovation",
]
_NEGATIVE_KW = [
    "miss", "misses", "missed", "downgrade", "downgraded", "loss", "losses",
    "lawsuit", "investigation", "recall", "warning", "bankruptcy", "crisis",
    "decline", "regulation", "fine", "violation", "scandal", "cut", "cuts",
    "lowers", "lowered", "weak", "disappoints", "disappointed", "slump",
]

def score_sentiment(text: str) -> str:
    t = text.lower()
    pos = sum(1 for w in _POSITIVE_KW if w in t)
    neg = sum(1 for w in _NEGATIVE_KW if w in t)
    if pos > neg:
        return "bullish"
    elif neg > pos:
        return "bearish"
    return "neutral"

def fetch_news(ticker_obj) -> list[str]:
    try:
        news = ticker_obj.news or []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        headlines = []
        for item in news[:10]:
            pub = item.get("content", {}).get("pubDate") or item.get("providerPublishTime", 0)
            if isinstance(pub, (int, float)):
                pub_dt = datetime.fromtimestamp(pub, tz=timezone.utc)
                if pub_dt < cutoff:
                    continue
            title = item.get("content", {}).get("title") or item.get("title", "")
            if title:
                headlines.append(title)
        return headlines[:5]
    except Exception:
        return []

# ---------------------------------------------------------------------------
# Financial health scores (free — yfinance balance sheet / income / cashflow)
# ---------------------------------------------------------------------------
def _safe_get(df, *keys):
    """Try multiple possible row labels, return first float found or None."""
    for k in keys:
        try:
            val = df.loc[k].iloc[0]
            if pd.notna(val) and val != 0:
                return float(val)
        except (KeyError, IndexError):
            pass
    return None

def _safe_get2(df, *keys):
    """Same but returns (current, prior) tuple for YoY comparisons."""
    for k in keys:
        try:
            row = df.loc[k]
            cur = float(row.iloc[0]) if pd.notna(row.iloc[0]) else None
            pri = float(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else None
            if cur is not None:
                return cur, pri
        except (KeyError, IndexError):
            pass
    return None, None


def calc_altman_z(tkr) -> dict | None:
    """
    Altman Z-Score for public companies.
    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
    Safe > 2.99 | Gray 1.81-2.99 | Distress < 1.81
    """
    try:
        bs = tkr.balance_sheet
        inc = tkr.income_stmt
        if bs is None or bs.empty or inc is None or inc.empty:
            return None

        total_assets = _safe_get(bs, "Total Assets")
        if not total_assets:
            return None

        cur_assets  = _safe_get(bs, "Current Assets")
        cur_liab    = _safe_get(bs, "Current Liabilities")
        ret_earn    = _safe_get(bs, "Retained Earnings")
        total_liab  = _safe_get(bs, "Total Liabilities Net Minority Interest",
                                    "Total Liabilities")
        ebit        = _safe_get(inc, "EBIT", "Operating Income")
        revenue     = _safe_get(inc, "Total Revenue", "Revenue")
        market_cap  = tkr.info.get("marketCap") if tkr.info else None

        working_cap = (cur_assets - cur_liab) if (cur_assets and cur_liab) else None

        x1 = working_cap / total_assets if working_cap is not None else 0
        x2 = ret_earn    / total_assets if ret_earn    else 0
        x3 = ebit        / total_assets if ebit        else 0
        x4 = (market_cap / total_liab)  if (market_cap and total_liab) else 0
        x5 = revenue     / total_assets if revenue     else 0

        z = round(1.2*x1 + 1.4*x2 + 3.3*x3 + 0.6*x4 + 1.0*x5, 2)
        if z > 2.99:
            zone = "safe"
        elif z > 1.81:
            zone = "gray"
        else:
            zone = "distress"

        return {"score": z, "zone": zone}
    except Exception:
        return None


def calc_piotroski(tkr) -> dict | None:
    """
    Piotroski F-Score (0-9). Higher = stronger fundamentals.
    >= 7 strong | 3-6 neutral | <= 2 weak
    """
    try:
        bs  = tkr.balance_sheet
        inc = tkr.income_stmt
        cf  = tkr.cashflow
        if any(x is None or (hasattr(x, 'empty') and x.empty) for x in [bs, inc, cf]):
            return None

        total_assets_c, total_assets_p = _safe_get2(bs, "Total Assets")
        if not total_assets_c:
            return None

        net_income_c, _  = _safe_get2(inc, "Net Income")
        ocf_c,  _        = _safe_get2(cf,  "Operating Cash Flow", "Cash Flow From Continuing Operating Activities")
        roa_c  = (net_income_c / total_assets_c) if (net_income_c and total_assets_c) else None

        net_income_p, _  = _safe_get2(inc, "Net Income")
        net_income_p = float(inc.loc["Net Income"].iloc[1]) if "Net Income" in inc.index and len(inc.loc["Net Income"]) > 1 else None
        roa_p = (net_income_p / total_assets_p) if (net_income_p and total_assets_p) else None

        gross_c, gross_p = _safe_get2(inc, "Gross Profit")
        rev_c,   rev_p   = _safe_get2(inc, "Total Revenue", "Revenue")

        lt_debt_c, lt_debt_p = _safe_get2(bs, "Long Term Debt")
        cur_assets_c, cur_assets_p = _safe_get2(bs, "Current Assets")
        cur_liab_c,   cur_liab_p  = _safe_get2(bs, "Current Liabilities")
        shares_c, shares_p = _safe_get2(bs, "Ordinary Shares Number", "Share Issued")

        cr_c = (cur_assets_c / cur_liab_c) if (cur_assets_c and cur_liab_c) else None
        cr_p = (cur_assets_p / cur_liab_p) if (cur_assets_p and cur_liab_p) else None
        lev_c = (lt_debt_c / total_assets_c) if (lt_debt_c and total_assets_c) else None
        lev_p = (lt_debt_p / total_assets_p) if (lt_debt_p and total_assets_p) else None
        gm_c  = (gross_c / rev_c) if (gross_c and rev_c) else None
        gm_p  = (gross_p / rev_p) if (gross_p and rev_p) else None
        at_c  = (rev_c / total_assets_c) if (rev_c and total_assets_c) else None
        at_p  = (rev_p / total_assets_p) if (rev_p and total_assets_p) else None
        accrual = ((ocf_c / total_assets_c) - roa_c) if (ocf_c and roa_c and total_assets_c) else None

        score = 0
        details = []

        # Profitability
        if roa_c is not None and roa_c > 0:       score += 1; details.append("ROA>0")
        if ocf_c is not None and ocf_c > 0:       score += 1; details.append("OCF>0")
        if roa_c and roa_p and roa_c > roa_p:     score += 1; details.append("ROA↑")
        if accrual is not None and accrual > 0:   score += 1; details.append("Quality")

        # Leverage / Liquidity
        if lev_c and lev_p and lev_c < lev_p:    score += 1; details.append("Debt↓")
        if cr_c  and cr_p  and cr_c  > cr_p:     score += 1; details.append("CR↑")
        if shares_c and shares_p and shares_c <= shares_p: score += 1; details.append("NoDilution")

        # Efficiency
        if gm_c and gm_p and gm_c > gm_p:        score += 1; details.append("Margin↑")
        if at_c and at_p and at_c > at_p:         score += 1; details.append("AssetTurn↑")

        if score >= 7:
            strength = "strong"
        elif score >= 3:
            strength = "neutral"
        else:
            strength = "weak"

        return {"score": score, "strength": strength, "signals": details}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Per-ticker fetch
# ---------------------------------------------------------------------------
def fetch_ticker(entry: dict) -> dict:
    symbol = entry["symbol"]
    buy_price = entry["buyPrice"]
    quantity = entry["quantity"]

    result = {
        "symbol": symbol,
        "name": entry.get("name", symbol),
        "sector": entry.get("sector", ""),
        "buy_price": buy_price,
        "quantity": quantity,
        "buy_date": entry.get("buyDate", ""),
        "cost_basis": round(buy_price * quantity, 2),
        "current_price": None,
        "change_pct_1d": None,
        "change_pct_7d": None,
        "change_pct_30d": None,
        "pnl_amount": None,
        "pnl_pct": None,
        "rsi_14": None,
        "week_52_high": None,
        "week_52_low": None,
        "pct_from_52w_high": None,
        "pct_from_52w_low": None,
        "market_cap": None,
        "pe_ratio": None,
        "forward_pe": None,
        "peg_ratio": None,
        "analyst_target": None,
        "analyst_upside": None,
        "recommendation_mean": None,
        "altman_z": None,
        "piotroski": None,
        "trend": "unknown",
        "news_headlines": [],
        "news_sentiment": "neutral",
        "error": None,
    }

    try:
        tkr = yf.Ticker(symbol)
        hist_1y = tkr.history(period="1y", interval="1d", auto_adjust=True)

        if hist_1y.empty:
            result["error"] = "no_data"
            return result

        closes = hist_1y["Close"]
        current = float(closes.iloc[-1])
        result["current_price"] = round(current, 4)

        # P&L vs buy price
        result["pnl_amount"] = round((current - buy_price) * quantity, 2)
        result["pnl_pct"] = round((current - buy_price) / buy_price * 100, 2)

        # Changes
        if len(closes) >= 2:
            result["change_pct_1d"] = round((closes.iloc[-1] / closes.iloc[-2] - 1) * 100, 2)
        if len(closes) >= 7:
            result["change_pct_7d"] = round((closes.iloc[-1] / closes.iloc[-7] - 1) * 100, 2)
        if len(closes) >= 30:
            result["change_pct_30d"] = round((closes.iloc[-1] / closes.iloc[-30] - 1) * 100, 2)

        # 52w range
        high52 = float(closes[-252:].max()) if len(closes) >= 252 else float(closes.max())
        low52 = float(closes[-252:].min()) if len(closes) >= 252 else float(closes.min())
        result["week_52_high"] = round(high52, 4)
        result["week_52_low"] = round(low52, 4)
        result["pct_from_52w_high"] = round((current - high52) / high52 * 100, 2)
        result["pct_from_52w_low"] = round((current - low52) / low52 * 100, 2)

        # RSI
        result["rsi_14"] = calc_rsi(closes)

        # Trend (SMA20 vs SMA50)
        if len(closes) >= 50:
            sma20 = float(closes.rolling(20).mean().iloc[-1])
            sma50 = float(closes.rolling(50).mean().iloc[-1])
            result["trend"] = "uptrend" if sma20 > sma50 else "downtrend"

        # Fundamentals
        info = tkr.info or {}
        result["market_cap"] = info.get("marketCap")
        result["pe_ratio"] = info.get("trailingPE")
        result["forward_pe"] = info.get("forwardPE")
        result["peg_ratio"] = info.get("pegRatio")
        result["analyst_target"] = info.get("targetMeanPrice")
        if result["analyst_target"] and current:
            result["analyst_upside"] = round((result["analyst_target"] - current) / current * 100, 2)
        result["recommendation_mean"] = info.get("recommendationMean")  # 1=strong buy, 5=strong sell

        # Financial health scores
        result["altman_z"]  = calc_altman_z(tkr)
        result["piotroski"] = calc_piotroski(tkr)

        # News
        headlines = fetch_news(tkr)
        result["news_headlines"] = headlines
        all_text = " ".join(headlines)
        result["news_sentiment"] = score_sentiment(all_text) if all_text else "neutral"

    except Exception as e:
        result["error"] = str(e)

    return result

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not os.path.exists(PORTFOLIO_FILE):
        print(f"ERROR: {PORTFOLIO_FILE} not found. No positions to analyze.", file=sys.stderr)
        sys.exit(1)

    portfolio = json.loads(open(PORTFOLIO_FILE, encoding="utf-8").read())
    if not portfolio:
        print("Portfolio is empty.", file=sys.stderr)
        sys.exit(0)

    symbols = [e["symbol"] for e in portfolio]
    print(f"Fetching data for {len(symbols)} positions: {', '.join(symbols)}")

    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_ticker, entry): entry["symbol"] for entry in portfolio}
        for fut in as_completed(futures):
            sym = futures[fut]
            try:
                r = fut.result()
                results.append(r)
                price = r.get("current_price")
                pnl = r.get("pnl_pct")
                rsi = r.get("rsi_14")
                print(f"  {sym}: price=${price} pnl={pnl:+.2f}% rsi={rsi}" if pnl is not None else f"  {sym}: {r.get('error','?')}")
            except Exception as e:
                print(f"  {sym}: ERROR {e}")

    # Sort by original portfolio order
    order = {e["symbol"]: i for i, e in enumerate(portfolio)}
    results.sort(key=lambda r: order.get(r["symbol"], 999))

    # Macro snapshot from market_context if available
    macro = {}
    mc_path = os.path.join(DATA_DIR, "market_context.json")
    if os.path.exists(mc_path):
        try:
            mc = json.loads(open(mc_path, encoding="utf-8").read())
            macro = mc.get("macro", {})
        except Exception:
            pass

    output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "positions": results,
        "macro": macro,
        "total_cost": round(sum(r["cost_basis"] for r in results), 2),
        "total_current_value": round(sum((r["current_price"] or 0) * r["quantity"] for r in results), 2),
    }
    output["total_pnl"] = round(output["total_current_value"] - output["total_cost"], 2)
    output["total_pnl_pct"] = round(output["total_pnl"] / output["total_cost"] * 100, 2) if output["total_cost"] else 0

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nOK → {OUTPUT_FILE}")
    print(f"Portfolio: cost=${output['total_cost']} | value=${output['total_current_value']} | P&L={output['total_pnl_pct']:+.2f}%")

if __name__ == "__main__":
    main()
