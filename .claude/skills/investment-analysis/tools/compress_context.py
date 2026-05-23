#!/usr/bin/env python3
"""
compress_context.py — Genera el bloque de datos comprimido para el MegaAgent.

Target: < 4,000 chars (vs ~13,700 inline). Reducción: ~70%.

Usage:
    python3 tools/compress_context.py
    python3 tools/compress_context.py --prev output/history/2026-05-21.json
    python3 tools/compress_context.py --prev output/history/2026-05-21.json --out /tmp/mega_context.txt

Si --prev no se pasa, se omite la sección PREVIOUS_THESES.
Si --out no se pasa, imprime a stdout.
"""

import argparse
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent


def load_json(path: str | Path) -> dict | list:
    p = Path(path)
    if not p.exists():
        print(f"[compress_context] WARN: {path} not found, skipping.", file=sys.stderr)
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def fmt_entry_quality(raw: str) -> str:
    """Trunca 'excellent — oversold' → 'excl-ovrs', 'good' → 'good', etc."""
    raw = (raw or "").lower()
    if "excellent" in raw and "oversold" in raw:
        return "excl-ovrs"
    if "excellent" in raw:
        return "excl"
    if "good" in raw:
        return "good"
    if "fair" in raw:
        return "fair"
    if "poor" in raw:
        return "poor"
    return raw[:8]


def fmt_trend(raw: str) -> str:
    raw = (raw or "").lower()
    if "downtrend" in raw:
        return "down"
    if "uptrend" in raw:
        return "up"
    if "mixed" in raw or "neutral" in raw:
        return "mix"
    return raw[:4]


def truncate(s: str, n: int) -> str:
    s = str(s or "")
    return s if len(s) <= n else s[: n - 1] + "…"


def build_macro_line(macro: dict) -> str:
    return (
        f"MACRO: VIX={macro.get('vix', '?')} "
        f"F&G={macro.get('fear_greed_value', '?')}({macro.get('fear_greed_label', '?')}) "
        f"Synthetic={macro.get('fear_greed_synthetic', '?')} "
        f"SPY={macro.get('spy_price', '?')} "
        f"SPY_RSI={macro.get('spy_rsi', '?')} "
        f"Regime={macro.get('market_regime', '?')} "
        f"Yield10y={macro.get('yield_10y', '?')} "
        f"YieldTrend={macro.get('yield_trend', '?')}"
    )


def fmt_altman_zone(raw: str | None) -> str:
    raw = (raw or "").lower()
    if "safe" in raw:    return "safe"
    if "gray" in raw:    return "gray"
    if "distress" in raw: return "dist"
    if "financial" in raw: return "fin"
    return "N/A"


def build_candidates_table(candidates: list) -> list[str]:
    lines = [
        "SCREENED_CANDIDATES (top 15 | sym|score|price|rsi|entry|trend|fpe|peg|earn_d|corr_grp|atr|z|piof)"
    ]
    for c in candidates[:15]:
        sym = c.get("symbol", "?")
        score = c.get("composite_score")
        score_s = f"{score:.0f}" if score is not None else "?"
        price = c.get("price", c.get("price_at_fetch", 0))
        rsi = c.get("rsi", 0)
        entry = fmt_entry_quality(c.get("entry_quality", ""))
        trend = fmt_trend(c.get("trend", ""))
        fpe = c.get("forward_pe")
        fpe_s = f"{fpe:.1f}" if fpe is not None else "?"
        peg = c.get("peg")
        peg_s = f"{peg:.2f}" if peg is not None else "?"
        earn = c.get("earnings_days_away", "?")
        corr = c.get("correlation_group", "?")
        atr = c.get("atr_14")
        atr_s = f"{atr:.2f}" if atr is not None else "?"
        z = fmt_altman_zone(c.get("altman_zone"))
        piof = c.get("piotroski")
        piof_s = str(piof) if piof is not None else "?"
        lines.append(
            f"  {sym}|{score_s}|{price:.2f}|{rsi:.0f}|{entry}|{trend}|{fpe_s}|{peg_s}|{earn}|{corr}|{atr_s}|{z}|{piof_s}"
        )
    return lines


def build_corr_warnings(warnings: list) -> list[str]:
    if not warnings:
        return []
    lines = ["CORRELATION_LIMITS (hard rule — max N picks per group):"]
    for w in warnings:
        group = w.get("group", "?")
        tickers = ",".join(w.get("all_candidates", []))
        max_a = w.get("max_allowed", "?")
        keep = ",".join(w.get("suggested_keep", []))
        cut = ",".join(w.get("suggested_cut", []))
        lines.append(
            f"  {group}[{tickers}] max={max_a} keep=[{keep}] cut=[{cut}]"
        )
    return lines


def build_news_block(news_map: dict, candidates: list) -> list[str]:
    # Only emit news for candidates in the screened list
    syms = {c["symbol"] for c in candidates[:15]}
    lines = ["NEWS (sym:[sentiment|rec $target] → h1 | h2 | kw)"]
    for sym, n in news_map.items():
        if sym not in syms:
            continue
        sent = n.get("sentiment", {}).get("label", "?") if isinstance(n.get("sentiment"), dict) else "?"
        rec = n.get("analyst_recommendation", "—") or "—"
        tgt_raw = n.get("analyst_target")
        tgt = f"${tgt_raw:.0f}" if tgt_raw else "—"
        headlines = n.get("key_news", [])
        h1 = truncate(headlines[0].get("title", "—") if headlines else "—", 58)
        h2 = truncate(headlines[1].get("title", "—") if len(headlines) > 1 else "—", 58)
        kw_raw = n.get("sentiment", {}).get("keywords", []) if isinstance(n.get("sentiment"), dict) else []
        kw = ",".join(k.get("word", "") for k in kw_raw[:3])
        lines.append(f"  {sym}:[{sent}|{rec} {tgt}] → {h1} | {h2} | [{kw}]")
    return lines


def build_sec_block(sec_results: list, candidates: list) -> list[str]:
    syms = {c["symbol"] for c in candidates[:15]}
    # Index by symbol for fast lookup
    sec_map = {r["symbol"]: r for r in sec_results if isinstance(r, dict)}
    lines = ["SEC_RISKS (sym: filing | risk1 ; risk2)"]
    for sym in [c["symbol"] for c in candidates[:15]]:
        if sym not in syms:
            continue
        r = sec_map.get(sym)
        if not r or r.get("error"):
            lines.append(f"  {sym}: no_filing")
            continue
        filing_date = (r.get("filing_date") or "")[:7]
        form = r.get("form", "?")
        factors = r.get("risk_factors", [])
        # Skip boilerplate bullets — forward-looking disclaimers, company intros, generic risk headers
        _BOILERPLATE = (
            "forward-looking", "undertake no obligation", "new information",
            "read the information", "business overview", "our mission",
            "our purpose", "readers should not consider", "additional risks and uncertainties",
            "our ciso", "cybersecurity program is led", "carefully consider the risks",
            "could also be harm", "in conjunction with", "since visa's early",
            "revolutionize commerce", "uplift everyone", "preeminent banking",
            "global diversified financial services", "financial holding company",
            "holding company whose",
        )
        relevant = [
            f for f in factors
            if len(f) > 80
            and not any(bp in f.lower() for bp in _BOILERPLATE)
        ]
        b1 = truncate(relevant[0], 80) if relevant else "—"
        b2 = truncate(relevant[1], 80) if len(relevant) > 1 else "—"
        lines.append(f"  {sym}: {form} {filing_date} | {b1} ; {b2}")
    return lines


def build_carry_forward_block(candidates: list, prices_snapshot: dict) -> list[str]:
    """Inject active positions that are NOT in today's screened candidates.

    These are picks from prior sessions whose theses are still valid but fell
    out of the top-15 screened list (RSI normalized, score dropped, etc.).
    The MegaAgent MUST include them in the report unless a thesis invalidator
    has explicitly been triggered.

    Max 5 carries to keep context overhead minimal (~400-600 chars).
    """
    active_path = SKILL_DIR / "data" / "active_positions.json"
    if not active_path.exists():
        return []
    try:
        active = json.loads(active_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not active:
        return []

    screened_syms = {c.get("symbol") for c in candidates[:15]}
    carries = [v for k, v in active.items() if k not in screened_syms]
    if not carries:
        return []

    lines = [
        "CARRY_FORWARD — Active positions NOT in today's screened top-15.",
        "RULE: KEEP these in the report unless a thesis_invalidator has been triggered.",
        "  sym|entry|now|ret%|status|position_size|thesis[:80]",
    ]
    for c in carries[:5]:
        sym = c.get("symbol", "?")
        entry = c.get("entry_price")
        entry_s = f"{entry:.2f}" if entry else "?"
        now_data = prices_snapshot.get(sym, {})
        now_price = now_data.get("price") if isinstance(now_data, dict) else None
        ret_s = f"{(now_price - entry) / entry * 100:+.1f}%" if now_price and entry else "?"
        now_s = f"{now_price:.2f}" if now_price else "?"
        status = c.get("thesis_status", "?")[:10]
        pos = c.get("position_size", "—") or "—"
        thesis = truncate(c.get("thesis", ""), 80)
        lines.append(f"  {sym}|{entry_s}|{now_s}|{ret_s}|{status}|{pos}|{thesis}")

    return lines


def build_theses_block(prev_path: str, prices_snapshot: dict) -> list[str]:
    if not prev_path:
        return []
    h = load_json(prev_path)
    if not h:
        return []
    picks = h.get("risk_adjusted_picks", h.get("picks", []))
    if not picks:
        return []
    report_date = h.get("date", Path(prev_path).stem)
    lines = [f"PREVIOUS_THESES (from {report_date})"]
    lines.append("  sym|entry|now|ret%|status|thesis[:60]|invalidators[:50]")
    for p in picks:
        if not isinstance(p, dict):
            continue
        sym = p.get("symbol", "?")
        entry = p.get("entry_price", 0)
        entry_s = f"{entry:.2f}" if entry else "?"
        now = prices_snapshot.get(sym, {})
        now_price = now.get("price") if isinstance(now, dict) else None
        ret_s = f"{(now_price - entry) / entry * 100:+.1f}%" if now_price and entry else "?"
        now_s = f"{now_price:.2f}" if now_price else "?"
        status = p.get("thesis_status", "?")[:10]
        thesis = truncate(p.get("thesis", ""), 50)
        inv_raw = p.get("thesis_invalidators", [])
        inv = truncate(inv_raw[0] if inv_raw else "—", 40)
        lines.append(f"  {sym}|{entry_s}|{now_s}|{ret_s}|{status}|{thesis}|{inv}")
    return lines


def main():
    parser = argparse.ArgumentParser(description="Compress MegaAgent input context")
    parser.add_argument("--prev", default=None, help="Path to previous history JSON for theses block")
    parser.add_argument("--out", default=None, help="Output file path (default: stdout)")
    args = parser.parse_args()

    mkt = load_json(SKILL_DIR / "data/market_context.json")
    news_raw = load_json(SKILL_DIR / "data/news_context.json")
    sec_raw = load_json(SKILL_DIR / "data/sec_risk_context.json")

    candidates = mkt.get("candidates", [])
    macro = mkt.get("macro", {})
    corr_warnings = mkt.get("correlation_warnings", [])
    news_map = news_raw.get("news", news_raw) if isinstance(news_raw, dict) else {}
    sec_results = sec_raw.get("results", []) if isinstance(sec_raw, dict) else []
    prices_snapshot = mkt.get("prices_snapshot", {})

    blocks: list[str] = []

    # 1. Macro
    blocks.append(build_macro_line(macro))

    # 2. Candidates table
    blocks.extend(build_candidates_table(candidates))

    # 3. Correlation limits
    blocks.extend(build_corr_warnings(corr_warnings))

    # 4. News
    blocks.extend(build_news_block(news_map, candidates))

    # 5. SEC risks
    blocks.extend(build_sec_block(sec_results, candidates))

    # 6. Previous theses
    blocks.extend(build_theses_block(args.prev, prices_snapshot))

    # 7. Carry-forward: active positions not in today's screened list
    blocks.extend(build_carry_forward_block(candidates, prices_snapshot))

    output = "\n".join(blocks)

    # Size check
    char_count = len(output)
    print(f"[compress_context] {char_count} chars ({char_count/13700*100:.0f}% of typical uncompressed)", file=sys.stderr)
    if char_count > 8000:
        print(f"[compress_context] WARN: output exceeds 8,000-char guardrail ({char_count} chars)", file=sys.stderr)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"[compress_context] Written to {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
