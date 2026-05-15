#!/usr/bin/env python3
"""
write_portfolio_report.py — Validates portfolio strategy JSON and writes it
to dashboard/public/data/portfolio_report.json using temp-then-rename.

Usage:
    python3 tools/write_portfolio_report.py data/portfolio_strategy.json
    echo '<json>' | python3 tools/write_portfolio_report.py -
"""

import json
import os
import sys
import tempfile
from datetime import datetime

MARKET_POSITION_FIELDS = [
    "name", "sector", "buy_price", "quantity", "buy_date", "cost_basis",
    "current_price", "change_pct_1d", "change_pct_7d", "change_pct_30d",
    "pnl_amount", "pnl_pct", "rsi_14", "week_52_high", "week_52_low",
    "pct_from_52w_high", "pct_from_52w_low", "market_cap", "pe_ratio",
    "forward_pe", "peg_ratio", "analyst_target", "analyst_upside",
    "recommendation_mean", "altman_z", "piotroski", "trend",
    "news_headlines", "news_sentiment", "error",
]

REQUIRED_TOP = [
    "generated_at", "portfolio_summary", "positions",
    "cross_position_insights", "priority_attention", "warnings",
]

REQUIRED_SUMMARY = [
    "total_positions", "total_cost", "total_current_value",
    "total_pnl", "total_pnl_pct", "overall_health", "immediate_actions_needed",
]

REQUIRED_POSITION = [
    "symbol", "action", "urgency", "position_health",
    "thesis_status", "reasoning",
]


def validate(data: dict) -> list[str]:
    errors = []
    for f in REQUIRED_TOP:
        if f not in data:
            errors.append(f"Missing top-level: '{f}'")
    if errors:
        return errors
    summary = data.get("portfolio_summary", {})
    for f in REQUIRED_SUMMARY:
        if f not in summary:
            errors.append(f"Missing portfolio_summary.{f}")
    positions = data.get("positions", [])
    if not isinstance(positions, list):
        errors.append("'positions' must be a list")
    else:
        for i, pos in enumerate(positions):
            for f in REQUIRED_POSITION:
                if f not in pos:
                    errors.append(f"positions[{i}] missing '{f}'")
    return errors


def atomic_write(path: str, content: str):
    dir_ = os.path.dirname(path) or "."
    os.makedirs(dir_, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise


def enrich_positions_with_market(repo: str, data: dict) -> dict:
    market_path = os.path.join(repo, "data", "portfolio_market.json")
    if not os.path.exists(market_path):
        return data

    try:
        market = json.loads(open(market_path, encoding="utf-8").read())
    except Exception:
        return data

    market_by_symbol = {
        pos.get("symbol"): pos
        for pos in market.get("positions", [])
        if pos.get("symbol")
    }

    enriched_positions = []
    for pos in data.get("positions", []):
        symbol = pos.get("symbol")
        market_pos = market_by_symbol.get(symbol, {})
        merged = dict(market_pos)
        merged.update(pos)
        for field in MARKET_POSITION_FIELDS:
            merged.setdefault(field, market_pos.get(field))
        enriched_positions.append(merged)

    data["positions"] = enriched_positions
    return data


def main():
    if len(sys.argv) < 2:
        print("Usage: write_portfolio_report.py <path_or_-> ", file=sys.stderr)
        sys.exit(1)

    src = sys.argv[1]
    if src == "-":
        raw = sys.stdin.read()
    else:
        if not os.path.exists(src):
            print(f"ERROR: file not found: {src}", file=sys.stderr)
            sys.exit(1)
        raw = open(src, encoding="utf-8").read()

    # Strip markdown fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    errors = validate(data)
    if errors:
        print("Validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  • {e}", file=sys.stderr)
        sys.exit(1)

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_out = os.path.join(repo, "dashboard", "public", "data", "portfolio_report.json")

    data = enrich_positions_with_market(repo, data)

    serialized = json.dumps(data, ensure_ascii=False, indent=2)

    atomic_write(dashboard_out, serialized)
    print(f"OK → {dashboard_out}")
    print(f"Positions: {data['portfolio_summary']['total_positions']} | "
          f"P&L: {data['portfolio_summary']['total_pnl_pct']:+.2f}% | "
          f"Attention needed: {data['portfolio_summary']['immediate_actions_needed']}")


if __name__ == "__main__":
    main()
