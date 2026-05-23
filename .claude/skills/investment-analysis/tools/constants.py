#!/usr/bin/env python3
"""
constants.py — Shared constants for the Tododeia investment-analysis pipeline.

Single source of truth for:
  - WATCHLISTS and _CORE ticker universe
  - CORRELATION_GROUPS and the derived _SYMBOL_TO_GROUP reverse-lookup
  - MAX_PICKS_PER_GROUP limit (enforced in both pre_fetch and assemble_report)
  - MACRO_TICKERS for macroeconomic proxy fetches

Import pattern (all tools in the same directory):
    from constants import CORRELATION_GROUPS, MAX_PICKS_PER_GROUP

Design rules:
  - No file I/O here — purely declarative data.
  - No circular imports — this module has zero local imports.
  - A ticker can belong to only ONE correlation group (primary driver wins).
"""

# ─── Core ticker universe ─────────────────────────────────────────────────────

_CORE = [
    "NVDA", "AMD", "TSM", "AMZN", "MSFT", "AAPL",
    "GOOGL", "META", "AVGO", "BAC", "JPM", "PLTR",
    "TSLA", "NFLX", "KMI",
]

# ─── Named watchlists ─────────────────────────────────────────────────────────
# Use with: python3 tools/pre_fetch.py --watchlist <name>
# Multiple names: python3 tools/pre_fetch.py --watchlist tech financials
# Individual tickers: python3 tools/pre_fetch.py INTC COIN GLD

WATCHLISTS: dict[str, list[str]] = {
    "default": _CORE,

    "tech": [
        "NVDA", "AMD", "TSM", "INTC", "QCOM", "ARM",
        "MSFT", "AAPL", "GOOGL", "META", "AMZN", "IBM",
        "AVGO", "AMAT", "ASML", "ASLM",
        "PLTR", "SNOW", "CRM", "NOW", "PANW",
        "NFLX", "TSLA", "RIVN", "SONY",
    ],

    "financials": [
        "JPM", "BAC", "GS", "MS", "WFC", "C",
        "V", "MA", "PYPL",
        "BLK", "BX",
        "NU", "SOFI",
    ],

    "consumer": [
        "DIS", "NFLX",
        "HD", "SBUX",
        "BABA", "MELI",
    ],

    "staples": [
        "WMT", "COST", "PG", "KO", "PEP",
    ],

    "industrials": [
        "CAT", "HON", "UPS", "BA",
    ],

    "telecom": [
        "T", "VZ",
    ],

    "reits": [
        "O", "PLD", "AMT", "MPW",
    ],

    "materials": [
        "GLD", "SLV", "GDX", "GDXJ",
        "XOM", "CVX", "COP", "KMI", "OXY",
        "FCX", "NEM",
    ],

    "healthcare": [
        "LLY", "UNH", "JNJ", "ABBV", "MRK",
        "AMGN", "GILD", "REGN", "MRNA", "PFE",
    ],

    "macro": [
        "SPY", "QQQ", "IWM", "DIA",
        "TLT", "GLD", "USO", "UUP",
    ],

    # Full extended: all of the above deduplicated (~65 tickers, ~3-4 min runtime)
    "all": sorted(set(
        _CORE +
        ["INTC", "QCOM", "ARM", "AMAT", "ASML", "ASLM", "SNOW", "CRM", "NOW", "PANW"] +
        ["JPM", "BAC", "GS", "MS", "WFC", "C", "V", "MA", "PYPL", "BLK", "BX"] +
        ["GLD", "SLV", "GDX", "XOM", "CVX", "COP", "OXY", "FCX", "NEM"] +
        ["LLY", "UNH", "JNJ", "ABBV", "MRK", "AMGN", "GILD", "REGN"] +
        # New additions (May 2026)
        ["SONY", "BABA", "RIVN", "MELI", "NU", "SOFI", "DIS", "HD", "SBUX", "IBM",
         "WMT", "COST", "PG", "KO", "PEP", "CAT", "HON", "UPS", "BA", "T", "VZ",
         "O", "PLD", "AMT", "MPW", "ORCL"]
    )),
}

# ─── Macro proxy tickers ──────────────────────────────────────────────────────

MACRO_TICKERS: list[str] = ["^VIX", "^TNX", "^GSPC", "^IRX"]

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

CORRELATION_GROUPS: dict[str, list[str]] = {
    "precious_metals":        ["GLD", "SLV", "GDX", "NEM"],
    "semiconductors":         ["NVDA", "AMD", "INTC", "QCOM", "TSM", "ARM", "AMAT", "ASML", "AVGO"],
    "big_tech":               ["MSFT", "AAPL", "GOOGL", "META", "AMZN", "IBM", "PLTR", "SONY"],
    "financials":             ["JPM", "BAC", "GS", "MS", "WFC", "C"],
    "payments":               ["V", "MA", "PYPL"],
    "healthcare":             ["JNJ", "ABBV", "MRK", "AMGN", "GILD", "REGN", "LLY", "UNH"],
    "staples":                ["WMT", "COST", "PG", "KO", "PEP"],
    "industrials":            ["CAT", "HON", "UPS", "BA"],
    "telecom":                ["T", "VZ"],
    "energy":                 ["XOM", "CVX", "COP", "OXY", "KMI"],
    "base_metals":            ["FCX"],
    "saas":                   ["CRM", "NOW", "SNOW", "PANW"],
    "enterprise_software":    ["ORCL", "IBM"],
    "asset_managers":         ["BLK", "BX"],
    "ev":                     ["TSLA", "RIVN"],
    "streaming":              ["NFLX", "DIS"],
    "ecommerce_global":       ["BABA", "MELI"],
    "fintech":                ["NU", "SOFI"],
    "consumer_discretionary": ["HD", "SBUX"],
    "reits":                  ["O", "PLD", "AMT", "MPW"],
}

# Reverse lookup: symbol → group name (built once at import time)
_SYMBOL_TO_GROUP: dict[str, str] = {
    sym: group
    for group, symbols in CORRELATION_GROUPS.items()
    for sym in symbols
}

# Maximum picks allowed per correlation group in a single report.
# Enforced as a warning (not a hard cut) so the MegaAgent has final judgment.
MAX_PICKS_PER_GROUP: int = 2
