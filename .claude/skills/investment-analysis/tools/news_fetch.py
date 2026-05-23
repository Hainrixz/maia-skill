#!/usr/bin/env python3
"""
news_fetch.py — Pre-fetch news + sentiment for screened candidates.

Reads candidates from data/market_context.json (output of pre_fetch.py).
Fetches yfinance news + analyst data + optional Reddit mentions in parallel.
Writes data/news_context.json for injection into the MegaAgent prompt.

Usage:
    python3 tools/news_fetch.py               # reads market_context.json
    python3 tools/news_fetch.py --top 12      # only top N candidates
    python3 tools/news_fetch.py --no-reddit   # skip Reddit (faster)

Output: data/news_context.json
"""

import argparse
import json
import logging
import os
import sys
import time
import warnings
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

import pandas as pd
import requests
import yfinance as yf

# VADER — handles negation, intensifiers, and punctuation ("not strong" ≠ "strong").
# Installed via: pip install vaderSentiment
# Falls back to keyword-based scoring if not available.
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as _VaderAnalyzer
    _vader = _VaderAnalyzer()
    _VADER_AVAILABLE = True
except ImportError:
    _vader = None
    _VADER_AVAILABLE = False

# Suppress yfinance noise globally (safe for threads)
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_DIR, "data")
MARKET_CTX = os.path.join(DATA_DIR, "market_context.json")
NEWS_CTX = os.path.join(DATA_DIR, "news_context.json")

# ---------------------------------------------------------------------------
# Sentiment — keyword-based, no external deps
# Adapted from spectral-galileo/src/spectral_galileo/analysis/sentiment_analysis.py
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

def _score_title(title: str) -> float:
    """Return sentiment score -1..1 based on keyword matching."""
    if not title:
        return 0.0
    t = title.lower()
    pos = sum(1 for kw in _POSITIVE_KW if kw in t)
    neg = sum(1 for kw in _NEGATIVE_KW if kw in t)
    total = pos + neg
    if total == 0:
        return 0.0
    return (pos - neg) / total  # range -1..1

def analyze_sentiment(news_list: list) -> dict:
    """
    Analyze sentiment of a news list.
    Primary: VADER (handles negation, punctuation, intensifiers — "not strong" scores as
    bearish, "GREAT!!!" scores higher than "great").
    Fallback: keyword-based scoring when vaderSentiment is not installed.
    Returns score (-1..1), label, and detected keywords.
    """
    if not news_list:
        return {"score": 0.0, "label": "neutral", "keywords": []}

    # Always collect keywords for context (independent of scoring method)
    keywords = []
    for item in news_list[:15]:
        t = (item.get("title") or "").lower()
        if not t:
            continue
        for kw in _POSITIVE_KW:
            if kw in t and (kw, "positive") not in keywords:
                keywords.append((kw, "positive"))
        for kw in _NEGATIVE_KW:
            if kw in t and (kw, "negative") not in keywords:
                keywords.append((kw, "negative"))

    if _VADER_AVAILABLE:
        # VADER: compound score per headline with recency weighting
        n = len(news_list)
        weighted_scores = []
        for i, item in enumerate(news_list[:15]):
            title = item.get("title", "")
            if not title:
                continue
            compound = _vader.polarity_scores(title)["compound"]
            weight = max(0.3, 1.0 - (i * 0.7 / n))  # most recent → weight=1.0
            weighted_scores.append(compound * weight)

        if weighted_scores:
            avg = sum(weighted_scores) / len(weighted_scores)
            label = "bullish" if avg > 0.05 else "bearish" if avg < -0.05 else "neutral"
            return {
                "score": round(avg, 3),
                "label": label,
                "keywords": [{"word": kw, "type": t} for kw, t in keywords[:6]],
                "method": "vader",
            }

    # Fallback: original keyword-based scoring
    scores = []
    n = len(news_list)
    for i, item in enumerate(news_list[:15]):
        title = item.get("title", "")
        if not title:
            continue
        score = _score_title(title)
        weight = max(0.3, 1.0 - (i * 0.7 / n))
        scores.append(score * weight)

    avg = sum(scores) / len(scores) if scores else 0.0
    if avg > 0.1:
        label = "bullish"
    elif avg < -0.1:
        label = "bearish"
    else:
        label = "neutral"

    return {
        "score": round(avg, 3),
        "label": label,
        "keywords": [{"word": kw, "type": t} for kw, t in keywords[:6]],
        "method": "keywords",
    }

# ---------------------------------------------------------------------------
# Reddit sentiment — no auth, public JSON API
# Adapted from spectral-galileo/src/spectral_galileo/external/reddit_sentiment.py
# ---------------------------------------------------------------------------
_REDDIT_UA = "Mozilla/5.0 (compatible; TododeiaNewsBot/1.0)"
_SUBREDDITS = ["wallstreetbets", "stocks", "investing", "SecurityAnalysis"]

def _reddit_search(subreddit: str, query: str, limit: int = 25) -> list:
    """Search one subreddit, return posts list."""
    try:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {"q": query, "restrict_sr": "on", "sort": "new", "limit": limit, "t": "day"}
        r = requests.get(url, params=params, headers={"User-Agent": _REDDIT_UA}, timeout=8)
        if r.status_code == 200:
            return [c["data"] for c in r.json()["data"]["children"]]
    except Exception:
        pass
    return []

def get_reddit_sentiment(symbol: str) -> dict:
    """
    Fetch Reddit mentions from WSB + stocks + investing (last 24h).
    Returns mentions count, score, and label.
    Times out at 15s total.
    """
    deadline = time.time() + 20
    query = f"${symbol} OR {symbol}"
    posts = []

    for sub in _SUBREDDITS:
        if time.time() > deadline:
            break
        posts.extend(_reddit_search(sub, query))
        time.sleep(0.3)

    if not posts:
        return {"mentions": 0, "score": 0.0, "label": "neutral", "buzz": "low"}

    cutoff = (datetime.now() - timedelta(hours=24)).timestamp()
    recent = [p for p in posts if p.get("created_utc", 0) >= cutoff]

    if not recent:
        return {"mentions": 0, "score": 0.0, "label": "neutral", "buzz": "low"}

    titles = [{"title": p.get("title", "")} for p in recent]
    sentiment = analyze_sentiment(titles)
    mentions = len(recent)
    buzz = "high" if mentions >= 10 else "medium" if mentions >= 4 else "low"

    return {
        "mentions": mentions,
        "score": sentiment["score"],
        "label": sentiment["label"],
        "buzz": buzz,
    }

# ---------------------------------------------------------------------------
# Google News RSS — more source diversity, no auth
# ---------------------------------------------------------------------------

def get_google_news(symbol: str) -> list:
    """
    Fetch up to 10 headlines from Google News RSS for the given ticker.
    Returns list of {title, publisher} dicts.
    Uses only stdlib xml.etree + requests — no new deps.
    """
    try:
        query = quote(f"{symbol} stock")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=8, headers={"User-Agent": _REDDIT_UA})
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item")[:12]:
            title_el = item.find("title")
            source_el = item.find("source")
            title = title_el.text if title_el is not None else ""
            publisher = source_el.text if source_el is not None else "Google News"
            if title:
                items.append({"title": title, "publisher": publisher})
        return items
    except Exception:
        return []


def get_general_market_news(n: int = 10) -> list:
    """
    Fetch top N general market/financial headlines from Google News RSS.
    Replaces the MegaAgent's manual fetch to https://finance.yahoo.com/news/.
    Returns list of {title, publisher} dicts.
    """
    try:
        url = "https://news.google.com/rss/search?q=stock+market+today&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=8, headers={"User-Agent": _REDDIT_UA})
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item")[:n]:
            title_el = item.find("title")
            source_el = item.find("source")
            title = title_el.text if title_el is not None else ""
            publisher = source_el.text if source_el is not None else "Google News"
            if title:
                items.append({"title": title, "publisher": publisher})
        return items
    except Exception:
        return []


def _merge_news(primary: list, secondary: list) -> list:
    """
    Merge two news lists, deduplicating by first-50-chars fingerprint.
    `primary` items (yfinance) take precedence.
    """
    seen = {item["title"][:50].lower() for item in primary}
    merged = list(primary)
    for item in secondary:
        fp = item["title"][:50].lower()
        if fp not in seen:
            seen.add(fp)
            merged.append(item)
    return merged


# ---------------------------------------------------------------------------
# Insider signal — SEC Form 4 via yfinance
# ---------------------------------------------------------------------------

def get_insider_signal(ticker: yf.Ticker) -> dict:
    """
    Count insider buys vs sells in the last 30 days from Form 4 filings.
    Returns {buys_30d, sells_30d, signal}.
    signal: "accumulating" | "distributing" | "mixed" | "none"
    """
    empty = {"buys_30d": 0, "sells_30d": 0, "signal": "none"}
    try:
        df = ticker.insider_transactions
        if df is None or df.empty:
            return empty
        # Normalize column names
        df.columns = [c.strip() for c in df.columns]
        date_col = next((c for c in df.columns if "date" in c.lower() or "start" in c.lower()), None)
        text_col = next((c for c in df.columns if "text" in c.lower() or "transaction" in c.lower()), None)
        if not text_col:
            return empty
        # Filter last 30 days
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
            df = df[df[date_col] >= cutoff]
        else:
            df = df.head(15)
        if df.empty:
            return empty
        buys = df[df[text_col].str.contains(r"Purchase|Buy|Acquisition", case=False, na=False, regex=True)].shape[0]
        sells = df[df[text_col].str.contains(r"Sale|Sell|Disposition", case=False, na=False, regex=True)].shape[0]
        if buys >= 2 and buys > sells:
            signal = "accumulating"
        elif sells >= 2 and sells > buys:
            signal = "distributing"
        elif buys > 0 or sells > 0:
            signal = "mixed"
        else:
            signal = "none"
        return {"buys_30d": int(buys), "sells_30d": int(sells), "signal": signal}
    except Exception:
        return empty


# ---------------------------------------------------------------------------
# Per-ticker news fetch
# ---------------------------------------------------------------------------
def fetch_news_for_ticker(symbol: str, include_reddit: bool = True) -> dict:
    """
    Fetch yfinance news + analyst rec + optional Reddit for one ticker.
    Returns a dict ready for news_context.json.
    """
    result = {
        "symbol": symbol,
        "key_news": [],
        "sentiment": {"score": 0.0, "label": "neutral", "keywords": []},
        "analyst_recommendation": None,
        "analyst_target": None,
        "num_analysts": None,
        "insider": {"buys_30d": 0, "sells_30d": 0, "signal": "none"},
        "recent_upgrades": [],
        "reddit": {"mentions": 0, "score": 0.0, "label": "neutral", "buzz": "low"},
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "error": None,
    }

    try:
        ticker = yf.Ticker(symbol)

        # ── yfinance news ─────────────────────────────────────────────────
        raw_news = ticker.news or []

        yf_news = []
        for n in raw_news[:15]:
            content = n.get("content", {}) if isinstance(n, dict) else {}
            title = content.get("title") or n.get("title", "")
            publisher = (
                content.get("provider", {}).get("displayName")
                or n.get("publisher", "")
            )
            if title:
                yf_news.append({"title": title, "publisher": publisher})

        # ── Google News RSS — deduplicated merge ──────────────────────────
        google_news = get_google_news(symbol)
        news_list = _merge_news(yf_news, google_news)

        result["key_news"] = news_list[:8]  # top 8 for context
        result["sentiment"] = analyze_sentiment(news_list)

        # ── Analyst data ─────────────────────────────────────────────────
        info = ticker.info or {}

        rec = info.get("recommendationKey")  # "buy" / "hold" / "sell" / "strong_buy" etc.
        if rec:
            result["analyst_recommendation"] = rec.lower().replace("_", " ")
        result["analyst_target"] = info.get("targetMeanPrice")
        result["num_analysts"] = info.get("numberOfAnalystOpinions")

        # ── Insider signal (Form 4 via yfinance) ──────────────────────────
        if not symbol.endswith("-USD"):  # skip crypto — no Form 4
            result["insider"] = get_insider_signal(ticker)
        # ── Analyst upgrades/downgrades (last 7 days) ─────────────────────────
        # An upgrade from Goldman/JPM this week is a high-conviction catalyst.
        # Replaces the MegaAgent's manual search for rating changes.
        if not symbol.endswith("-USD"):
            try:
                ud = ticker.upgrades_downgrades
                if ud is not None and not ud.empty:
                    idx = pd.to_datetime(ud.index, utc=True)
                    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)
                    mask = idx >= cutoff
                    recent_ud = ud[mask]
                    result["recent_upgrades"] = [
                        {
                            "firm": str(row.get("Firm", "")),
                            "action": str(row.get("Action", "")),
                            "from_grade": str(row.get("FromGrade", "")),
                            "to_grade": str(row.get("ToGrade", "")),
                        }
                        for _, row in recent_ud.iterrows()
                    ][:5]  # max 5 — enough for context without bloating the prompt
            except Exception:
                pass  # upgrades are optional — fail silently
    except Exception as e:
        result["error"] = str(e)

    # ── Reddit ────────────────────────────────────────────────────────────
    if include_reddit and not symbol.endswith("-USD"):  # skip crypto (no Reddit ticker symbol)
        result["reddit"] = get_reddit_sentiment(symbol)

    return result

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Pre-fetch news + sentiment for screened candidates")
    parser.add_argument("--top", type=int, default=0, help="Only fetch top N candidates (0 = all screened)")
    parser.add_argument("--no-reddit", action="store_true", help="Skip Reddit sentiment (faster, ~30s saved)")
    parser.add_argument("--workers", type=int, default=8, help="Parallel workers (default: 8)")
    args = parser.parse_args()

    include_reddit = not args.no_reddit

    # ── Load candidates from market_context.json ──────────────────────────
    if not os.path.exists(MARKET_CTX):
        print(f"[news_fetch] ERROR: {MARKET_CTX} not found — run pre_fetch.py first", file=sys.stderr)
        sys.exit(1)

    with open(MARKET_CTX) as f:
        ctx = json.load(f)

    candidates = ctx.get("candidates", [])
    if args.top > 0:
        candidates = candidates[: args.top]

    symbols = [c["symbol"] for c in candidates]

    print(
        f"[news_fetch] {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} — "
        f"{len(symbols)} tickers  reddit={'ON' if include_reddit else 'OFF'}  workers={args.workers}",
        file=sys.stderr,
    )

    # ── Parallel fetch ────────────────────────────────────────────────────
    results: dict[str, dict] = {}
    start = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_news_for_ticker, sym, include_reddit): sym for sym in symbols}
        done = 0
        for future in as_completed(futures):
            sym = futures[future]
            try:
                data = future.result()
                results[sym] = data
                sentiment_label = data["sentiment"]["label"]
                reddit_buzz = data["reddit"]["buzz"] if include_reddit else "—"
                insider_signal = data.get("insider", {}).get("signal", "—")
                print(
                    f"  {sym:10} sentiment={sentiment_label:8} reddit_buzz={reddit_buzz}  "
                    f"news={len(data['key_news'])}  analyst={data['analyst_recommendation'] or '—'}  insider={insider_signal}",
                    file=sys.stderr,
                )
            except Exception as e:
                results[sym] = {"symbol": sym, "error": str(e)}
                print(f"  {sym:10} ERROR: {e}", file=sys.stderr)
            done += 1

    elapsed = time.time() - start

    # ── General market headlines (replaces MegaAgent fetch to /news/) ────
    print("[news_fetch] Fetching general market headlines...", file=sys.stderr)
    market_headlines = get_general_market_news(n=10)
    print(f"[news_fetch] Market headlines: {len(market_headlines)} fetched", file=sys.stderr)

    # ── Write output ──────────────────────────────────────────────────────
    output = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tickers_fetched": len(results),
        "reddit_enabled": include_reddit,
        "elapsed_seconds": round(elapsed, 1),
        "market_headlines": market_headlines,
        "news": results,
    }

    tmp_path = NEWS_CTX + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    os.replace(tmp_path, NEWS_CTX)

    size_kb = os.path.getsize(NEWS_CTX) // 1024
    print(
        f"[news_fetch] ✓ Written → {NEWS_CTX}  ({size_kb:,} KB)  elapsed={elapsed:.1f}s",
        file=sys.stderr,
    )

    # ── Print compact summary for orchestrator ────────────────────────────
    print("\n=== NEWS CONTEXT SUMMARY ===")
    for sym in symbols:
        d = results.get(sym, {})
        if d.get("error"):
            print(f"  {sym}: ERROR — {d['error']}")
            continue
        news_titles = [n["title"][:80] for n in d.get("key_news", [])[:3]]
        label = d["sentiment"]["label"]
        reddit = d.get("reddit", {})
        insider = d.get("insider", {})
        kws = [k["word"] for k in d["sentiment"].get("keywords", [])[:3]]
        analyst = d.get("analyst_recommendation") or "—"
        target = d.get("analyst_target")
        target_str = f" target=${target}" if target else ""
        insider_str = f"  insider={insider.get('signal','—')}({insider.get('buys_30d',0)}B/{insider.get('sells_30d',0)}S)" if insider.get('signal', 'none') != 'none' else ""
        print(f"  {sym:10} [{label:8}] analyst={analyst}{target_str}  reddit={reddit.get('buzz','—')}/{reddit.get('mentions',0)}{insider_str}  kw={kws}")
        for t in news_titles:
            print(f"             → {t}")

if __name__ == "__main__":
    main()
