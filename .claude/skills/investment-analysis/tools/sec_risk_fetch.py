#!/usr/bin/env python3
"""
sec_risk_fetch.py — Fetch latest SEC filing risk factors (free, no API key).

Reads tickers from data/market_context.json by default, fetches latest 10-K/20-F/40-F
per ticker, extracts Item 1A Risk Factors text, and writes a compact JSON context file
for prompt injection.

Usage:
    python3 tools/sec_risk_fetch.py
    python3 tools/sec_risk_fetch.py --top 15
    python3 tools/sec_risk_fetch.py --symbols NVDA AMD MSFT
    python3 tools/sec_risk_fetch.py --out data/sec_risk_context.json

Output:
    data/sec_risk_context.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html import unescape
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

import yfinance as yf


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "data")
MARKET_CONTEXT = os.path.join(DATA_DIR, "market_context.json")
OUT_PATH = os.path.join(DATA_DIR, "sec_risk_context.json")
TICKER_CACHE = os.path.join(DATA_DIR, "sec_company_tickers_cache.json")

SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_no}/{primary_doc}"

# SEC asks for a descriptive User-Agent with contact info.
SEC_USER_AGENT = os.environ.get(
    "SEC_USER_AGENT",
    "TododeiaRiskFetcher/1.0 (github.com/modCarlos/maia-skill; contact: support@example.com)",
)


def fetch_url_text(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": SEC_USER_AGENT, "Accept": "application/json,text/html,*/*"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def fetch_url_json(url: str, timeout: int = 20) -> dict:
    return json.loads(fetch_url_text(url, timeout=timeout))


def load_market_symbols(path: str, top: int) -> list[str]:
    if not os.path.exists(path):
        return []
    data = json.loads(open(path, encoding="utf-8").read())

    symbols: list[str] = []
    candidates = data.get("candidates") or []
    if candidates:
        for c in candidates[:top]:
            sym = (c.get("symbol") or "").strip().upper()
            if sym and sym not in symbols:
                symbols.append(sym)
    else:
        snapshot = data.get("prices_snapshot") or {}
        for sym in snapshot.keys():
            s = str(sym).strip().upper()
            if s and s not in symbols:
                symbols.append(s)

    return symbols


def load_ticker_to_cik(force_refresh: bool = False) -> dict[str, str]:
    os.makedirs(DATA_DIR, exist_ok=True)

    # Cache TTL: 7 days
    cache_ttl_sec = 7 * 24 * 3600
    if (not force_refresh) and os.path.exists(TICKER_CACHE):
        age = time.time() - os.path.getmtime(TICKER_CACHE)
        if age <= cache_ttl_sec:
            try:
                return json.loads(open(TICKER_CACHE, encoding="utf-8").read())
            except Exception:
                pass

    raw = fetch_url_json(SEC_TICKER_URL)
    mapping: dict[str, str] = {}
    for _, row in raw.items():
        ticker = str(row.get("ticker", "")).upper().strip()
        cik_num = row.get("cik_str")
        if not ticker or cik_num is None:
            continue
        mapping[ticker] = str(cik_num).zfill(10)

    with open(TICKER_CACHE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    return mapping


def latest_yf_annual_filing(symbol: str) -> dict | None:
    """Fallback: use yfinance SEC filings metadata and Yahoo-hosted filing HTML."""
    try:
        filings = yf.Ticker(symbol).sec_filings or []
        preferred = {"10-K", "20-F", "40-F"}
        for f in filings:
            form = (f.get("type") or "").strip().upper()
            if form not in preferred:
                continue

            exhibits = f.get("exhibits") or {}
            filing_url = exhibits.get(form) or f.get("edgarUrl")
            if not filing_url:
                continue

            filing_date = str(f.get("date")) if f.get("date") is not None else None
            return {
                "form": form,
                "filing_date": filing_date,
                "accession": None,
                "primary_doc": None,
                "filing_url": filing_url,
                "provider": "yfinance",
            }
    except Exception:
        return None

    return None


def latest_filing_meta(cik10: str) -> dict | None:
    sub_url = SEC_SUBMISSIONS_URL.format(cik=cik10)
    data = fetch_url_json(sub_url)

    filings = (((data.get("filings") or {}).get("recent")) or {})
    forms = filings.get("form") or []
    accs = filings.get("accessionNumber") or []
    primary_docs = filings.get("primaryDocument") or []
    filing_dates = filings.get("filingDate") or []

    preferred_forms = {"10-K", "20-F", "40-F"}
    for i, form in enumerate(forms):
        if form not in preferred_forms:
            continue
        try:
            accession = accs[i]
            primary_doc = primary_docs[i]
            filing_date = filing_dates[i]
        except Exception:
            continue

        cik_int = str(int(cik10))
        acc_no = str(accession).replace("-", "")
        filing_url = SEC_ARCHIVES_BASE.format(cik_int=cik_int, acc_no=acc_no, primary_doc=primary_doc)
        return {
            "form": form,
            "filing_date": filing_date,
            "accession": accession,
            "primary_doc": primary_doc,
            "filing_url": filing_url,
        }

    return None


def strip_html(text: str) -> str:
    # Remove scripts/styles first
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    # Remove all tags
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_item_1a_section(raw_html: str) -> str:
    # Work on lowercased copy for indices, then slice original for context.
    lower = raw_html.lower()

    start_patterns = [
        r"item\s*1a\.?\s*risk\s*factors",
        r"risk\s*factors\s*item\s*1a",
        r"item\s*1a\.?",
        r"risk\s*factors",
    ]
    end_patterns = [
        r"item\s*1b\.?",
        r"unresolved\s*staff\s*comments",
        r"item\s*2\.?\s*properties",
        r"item\s*2\.?",
    ]

    start_idx = -1
    for pat in start_patterns:
        m = re.search(pat, lower)
        if m:
            start_idx = m.start()
            break

    if start_idx == -1:
        return ""

    tail = lower[start_idx + 20 :]
    end_idx = -1
    for pat in end_patterns:
        m = re.search(pat, tail)
        if m:
            end_idx = start_idx + 20 + m.start()
            break

    if end_idx == -1:
        end_idx = min(len(raw_html), start_idx + 220000)

    section = raw_html[start_idx:end_idx]
    cleaned = strip_html(section)

    # Sometimes table-of-contents matches occur first; prefer a longer body slice.
    if len(cleaned) < 1200:
        risk_hits = list(re.finditer(r"risk\s*factors", lower))
        for hit in risk_hits[1:5]:
            s2 = hit.start()
            tail2 = lower[s2 + 20 :]
            e2 = -1
            for pat in end_patterns:
                m2 = re.search(pat, tail2)
                if m2:
                    e2 = s2 + 20 + m2.start()
                    break
            if e2 == -1:
                e2 = min(len(raw_html), s2 + 220000)
            candidate = strip_html(raw_html[s2:e2])
            if len(candidate) > len(cleaned):
                cleaned = candidate

    return cleaned


def summarize_risk_factors(section_text: str, max_items: int = 4) -> list[str]:
    if not section_text:
        return []

    # Split into rough sentences; keep meaningful ones.
    parts = re.split(r"(?<=[.!?])\s+", section_text)
    cleaned: list[str] = []
    for p in parts:
        s = p.strip(" -:\n\t")
        if len(s) < 80:
            continue
        if len(s) > 320:
            s = s[:317].rstrip() + "..."
        # Skip boilerplate headers
        if re.search(r"item\s*1a|risk\s*factors", s, flags=re.I):
            continue
        if s not in cleaned:
            cleaned.append(s)
        if len(cleaned) >= max_items:
            break

    return cleaned


def fetch_risks_for_symbol(symbol: str, ticker_to_cik: dict[str, str]) -> dict:
    out = {
        "symbol": symbol,
        "cik": None,
        "form": None,
        "filing_date": None,
        "source_url": None,
        "risk_factors": [],
        "error": None,
    }

    cik = ticker_to_cik.get(symbol)
    if cik:
        out["cik"] = cik

    try:
        meta = None
        if cik:
            try:
                meta = latest_filing_meta(cik)
            except Exception:
                meta = None

        # Fallback path when SEC lookup is unavailable (e.g. HTTP 403) or no annual filing found.
        if not meta:
            meta = latest_yf_annual_filing(symbol)

        if not meta:
            out["error"] = "no_annual_filing_found"
            return out

        out["form"] = meta["form"]
        out["filing_date"] = meta["filing_date"]
        out["source_url"] = meta["filing_url"]

        html = fetch_url_text(meta["filing_url"], timeout=25)
        section = extract_item_1a_section(html)
        risks = summarize_risk_factors(section)
        if not risks:
            out["error"] = "item_1a_not_extracted"
            return out

        out["risk_factors"] = risks
        return out

    except (HTTPError, URLError, TimeoutError) as e:
        out["error"] = f"network_error: {e}"
        return out
    except Exception as e:
        out["error"] = f"unexpected_error: {e}"
        return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch SEC risk factors for tickers")
    parser.add_argument("--top", type=int, default=15, help="Top N candidates from market_context (default: 15)")
    parser.add_argument("--symbols", nargs="*", default=None, help="Explicit tickers (overrides market_context)")
    parser.add_argument("--out", default=OUT_PATH, help="Output JSON path")
    parser.add_argument("--force-refresh-cik", action="store_true", help="Refresh SEC ticker->CIK cache")
    args = parser.parse_args()

    if args.symbols:
        symbols = []
        for s in args.symbols:
            t = s.strip().upper()
            if t and t not in symbols:
                symbols.append(t)
    else:
        symbols = load_market_symbols(MARKET_CONTEXT, args.top)

    if not symbols:
        print("ERROR: no symbols to process", file=sys.stderr)
        return 1

    print(f"[sec_risk_fetch] processing {len(symbols)} tickers: {', '.join(symbols)}")

    try:
        ticker_to_cik = load_ticker_to_cik(force_refresh=args.force_refresh_cik)
    except Exception as e:
        ticker_to_cik = {}
        print(f"[sec_risk_fetch] warning: SEC ticker map unavailable ({e}); using yfinance fallback")

    results = []
    for i, sym in enumerate(symbols):
        # Polite pacing for SEC endpoints.
        if i > 0:
            time.sleep(0.25)

        row = fetch_risks_for_symbol(sym, ticker_to_cik)
        results.append(row)

        if row["error"]:
            print(f"  {sym}: {row['error']}")
        else:
            print(f"  {sym}: {row['form']} {row['filing_date']} ({len(row['risk_factors'])} risks)")

    out = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "SEC EDGAR",
        "top": args.top,
        "symbols": symbols,
        "results": results,
    }

    out_path = args.out
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in results if not r["error"])
    print(f"[sec_risk_fetch] OK -> {out_path} ({ok}/{len(results)} with extracted risk factors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
