#!/usr/bin/env python3
"""Normalize MegaAgent strategy output and write the final report.

This script is the local post-processing layer that keeps the LLM focused on
strategy while Python handles everything mechanical:

- recompute risk_adjusted_score deterministically
- normalize held-symbol recommendations to ADD/TRIM/HOLD
- enforce correlation-group limits
- fill missing pick fields from sectors / trailing stops / portfolio data
- validate and write the final report via write_report.py
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SKILL_DIR.parent.parent.parent
DATA_DIR = SKILL_DIR / "data"
DEFAULT_OUT_DIR = Path("/tmp/tododeia")
from constants import MAX_PICKS_PER_GROUP  # single source of truth: tools/constants.py


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_input(path: str) -> Any:
    if path == "-":
        return json.loads(sys.stdin.read())
    return read_json(Path(path))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_number(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isnan(float(value)):
            return default
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace("$", "").replace(",", "").replace("%", "")
        if not cleaned:
            return default
        try:
            return float(cleaned)
        except ValueError:
            return default
    return default


def clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


def normalize_risk_profile(value: str | None) -> str:
    mapping = {
        "conservative": "conservative",
        "conservador": "conservative",
        "moderate": "moderate",
        "moderado": "moderate",
        "aggressive": "aggressive",
        "agresivo": "aggressive",
    }
    if not value:
        return "moderate"
    return mapping.get(value.strip().lower(), value.strip().lower())


def profile_base_size(profile: str) -> float:
    return {
        "conservative": 4.0,
        "moderate": 6.0,
        "aggressive": 8.0,
    }.get(profile, 6.0)


def profile_target_multiplier(profile: str) -> float:
    return {
        "conservative": 1.18,
        "moderate": 1.25,
        "aggressive": 1.35,
    }.get(profile, 1.25)


def fallback_allocation(profile: str) -> dict[str, int]:
    return {
        "conservative": {"stocks": 50, "materials": 15, "cash": 35},
        "moderate": {"stocks": 65, "materials": 20, "cash": 15},
        "aggressive": {"stocks": 80, "materials": 10, "cash": 10},
    }.get(profile, {"stocks": 65, "materials": 20, "cash": 15})


def fallback_macro_environment(market_context: dict[str, Any]) -> dict[str, Any]:
    macro = market_context.get("macro") or {}
    regime = str(macro.get("market_regime") or macro.get("regime") or "MIXED").upper()
    spy_price = parse_number(macro.get("spy_price"))
    spy_rsi = parse_number(macro.get("spy_rsi"))
    vix = parse_number(macro.get("vix"))
    yield_trend = str(macro.get("yield_trend") or "stable").lower()

    interest_rate_outlook = "rising" if yield_trend == "rising" else "falling" if yield_trend == "falling" else "stable"
    inflation_outlook = "rising" if yield_trend == "rising" else "falling" if yield_trend == "falling" else "stable"

    return {
        "summary": (
            f"Fallback macro view: {regime} regime, SPY at {spy_price:.2f} if available, "
            f"RSI {spy_rsi:.1f} and VIX {vix:.1f} favor a selective approach."
            if spy_price is not None and spy_rsi is not None and vix is not None
            else f"Fallback macro view: {regime} regime with limited market context."
        ),
        "interest_rate_outlook": interest_rate_outlook,
        "inflation_outlook": inflation_outlook,
        "geopolitical_risk": "medium",
        "key_factors": [
            f"Regime={regime}",
            f"SPY RSI={spy_rsi if spy_rsi is not None else 'N/A'}",
            f"VIX={vix if vix is not None else 'N/A'}",
        ],
    }


def fallback_cross_sector_insights(market_context: dict[str, Any]) -> list[dict[str, str]]:
    macro = market_context.get("macro") or {}
    regime = str(macro.get("market_regime") or macro.get("regime") or "MIXED").upper()
    return [
        {
            "insight": f"Fallback synthesis: the market is in a {regime.lower()} regime and the strategy agent output was unavailable.",
            "implication": "Use the deterministic sector ranking and keep allocations conservative until a fresh strategy pass is available.",
        }
    ]


def fallback_picks(sectors: dict[str, Any], risk_profile: str, market_context: dict[str, Any]) -> list[dict[str, Any]]:
    assets: list[dict[str, Any]] = []
    for sector_key in ("stocks", "materials"):
        sector_data = sectors.get(sector_key) or {}
        for asset in sector_data.get("assets", []):
            if isinstance(asset, dict) and asset.get("symbol"):
                assets.append({"sector_key": sector_key, **asset})

    if not assets:
        return []

    target_mult = profile_target_multiplier(risk_profile)
    picks: list[dict[str, Any]] = []
    for idx, asset in enumerate(assets[:8], start=1):
        symbol = asset.get("symbol")
        current_price = parse_number(asset.get("current_price")) or parse_number(asset.get("technicals", {}).get("key_support")) or 0.0
        confidence = 8.5 if "excellent" in str(asset.get("reasoning", "")).lower() else 7.5 if "good" in str(asset.get("reasoning", "")).lower() else 6.5
        risk_score = 3.0 if asset.get("watchlist") in {"staples", "healthcare", "materials"} else 4.5
        target_12m = round(current_price * target_mult, 2) if current_price else None
        stop_loss = round(current_price * 0.93, 2) if current_price else None
        rr = ((target_12m - current_price) / (current_price - stop_loss)) if current_price and stop_loss and target_12m and current_price > stop_loss else 2.0
        rec = "buy"
        if risk_profile == "conservative" and idx > 4:
            rec = "hold"

        picks.append(
            {
                "rank": idx,
                "name": asset.get("name", symbol),
                "symbol": symbol,
                "sector": asset.get("watchlist") or asset.get("sector") or asset.get("sector_key") or "unknown",
                "confidence": confidence,
                "risk_score": risk_score,
                "recommendation": rec,
                "reasoning": asset.get("reasoning") or asset.get("sector_summary") or "Deterministic fallback ranking from pre-fetched candidates.",
                "position_size": f"{max(2.0, profile_base_size(risk_profile) - (idx - 1) * 0.5):.0f}%",
                "entry_price": current_price,
                "stop_loss": stop_loss,
                "target_12m": target_12m,
                "risk_reward_ratio": round(rr, 2) if rr is not None else 2.0,
                "thesis": asset.get("reasoning") or asset.get("sector_summary") or "Fallback thesis generated because the strategy analysis was unavailable.",
                "thesis_invalidators": ["Strategy analysis unavailable", "New catalyst or thesis break not yet reassessed"],
                "thesis_status": "new",
                "financial_health": asset.get("financial_health") or {
                    "altman_z": None,
                    "altman_zone": "N/A",
                    "piotroski": None,
                    "piotroski_strength": "N/A",
                    "health_note": "Fallback output — financial health not synthesized by the strategy agent.",
                },
                "key_news": asset.get("key_news") or [],
                "social_highlights": asset.get("social_highlights") or [],
                "technicals": asset.get("technicals") or {},
                "valuation": asset.get("valuation") or {},
                "fundamentals": asset.get("fundamentals") or {},
            }
        )

    return picks


def load_held_symbols() -> set[str]:
    symbols: set[str] = set()
    portfolio_path = PROJECT_ROOT / "data" / "portfolio_market.json"
    active_path = DATA_DIR / "active_positions.json"

    for path in (portfolio_path, active_path):
        raw = read_json(path)
        if path == portfolio_path:
            if isinstance(raw, dict):
                positions = raw.get("positions") or []
            elif isinstance(raw, list):
                positions = raw
            else:
                positions = []
        else:
            if isinstance(raw, dict):
                positions = list(raw.values())
            elif isinstance(raw, list):
                positions = raw
            else:
                positions = []

        for position in positions or []:
            if isinstance(position, dict):
                sym = position.get("symbol") or position.get("ticker")
                if sym:
                    symbols.add(str(sym).upper())

    return symbols


def load_trailing_stops() -> dict[str, Any]:
    path = DATA_DIR / "trailing_stops.json"
    raw = read_json(path, {})
    if isinstance(raw, dict):
        return raw.get("stops") or {}
    return {}


def build_asset_index(sectors: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for sector_key, sector_data in sectors.items():
        if not isinstance(sector_data, dict):
            continue
        for asset in sector_data.get("assets", []) or []:
            if not isinstance(asset, dict):
                continue
            symbol = asset.get("symbol")
            if symbol:
                index[str(symbol).upper()] = {"sector_key": sector_key, **asset}
    return index


def normalize_recommendation(raw: Any, held: bool) -> str:
    rec = str(raw or "hold").strip().lower()
    synonyms = {
        "strong buy": "buy",
        "strong sell": "sell",
        "neutral": "hold",
        "trim": "trim",
        "add": "add",
        "hold": "hold",
        "buy": "buy",
        "sell": "sell",
    }
    rec = synonyms.get(rec, rec)

    if held:
        if rec in {"buy", "add"}:
            return "add"
        if rec in {"sell", "trim"}:
            return "trim"
        return "hold"

    if rec == "add":
        return "buy"
    if rec == "trim":
        return "sell"
    if rec not in {"buy", "sell", "hold"}:
        return "hold"
    return rec


def normalize_position_size(raw: Any, profile: str, rank: int) -> str:
    if isinstance(raw, str) and raw.strip().endswith("%"):
        return raw.strip()
    size = parse_number(raw)
    if size is None:
        size = max(1.0, profile_base_size(profile) - (rank - 1) * 0.5)
    if size <= 1:
        return f"{size:.1f}%"
    return f"{size:.0f}%"


def infer_sector(asset: dict[str, Any], pick: dict[str, Any]) -> str:
    return str(pick.get("sector") or asset.get("watchlist") or asset.get("sector_key") or asset.get("sector") or "unknown")


def derive_financial_health(pick: dict[str, Any], asset: dict[str, Any]) -> dict[str, Any]:
    health = pick.get("financial_health") or asset.get("financial_health") or {}
    if not isinstance(health, dict):
        health = {}

    altman_z = health.get("altman_z")
    altman_zone = health.get("altman_zone") or health.get("zone") or "N/A"
    piotroski = health.get("piotroski")
    piotr_strength = health.get("piotroski_strength") or health.get("strength") or "N/A"

    if isinstance(altman_zone, str) and altman_zone.lower().startswith("financial"):
        altman_zone = "N/A"

    note = health.get("health_note") or health.get("note")
    if not note:
        if altman_zone == "distress":
            note = "Altman distress zone — thesis must explicitly justify turnaround risk."
        elif piotr_strength == "weak" or (isinstance(piotroski, (int, float)) and piotroski <= 2):
            note = "Weak Piotroski score — fundamentals deserve tighter risk controls."
        elif altman_zone == "safe" and piotr_strength == "strong":
            note = "Strong balance sheet and operating quality."
        else:
            note = "Financial health data carried through from pre-fetched context."

    return {
        "altman_z": altman_z,
        "altman_zone": altman_zone,
        "piotroski": piotroski,
        "piotroski_strength": piotr_strength,
        "health_note": note,
    }


def merge_report_fields(pick: dict[str, Any], asset: dict[str, Any]) -> dict[str, Any]:
    merged = dict(asset)
    merged.update(pick)
    return merged


def normalize_picks(
    picks: list[dict[str, Any]],
    sectors: dict[str, Any],
    risk_profile: str,
    market_context: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    asset_index = build_asset_index(sectors)
    trailing_stops = load_trailing_stops()
    held_symbols = load_held_symbols()

    normalized: list[dict[str, Any]] = []
    warnings: list[str] = []

    for raw_pick in picks:
        if not isinstance(raw_pick, dict):
            continue

        symbol = str(raw_pick.get("symbol") or "").upper().strip()
        if not symbol:
            continue

        asset = asset_index.get(symbol, {})
        merged = merge_report_fields(raw_pick, asset)
        held = symbol in held_symbols

        rec = normalize_recommendation(merged.get("recommendation"), held)
        confidence = parse_number(merged.get("confidence"), 6.5 if not held else 6.8) or 6.5
        risk_score = parse_number(merged.get("risk_score"), 4.0) or 4.0
        risk_adjusted = clamp(round(confidence - (risk_score * 0.3), 1))

        asset_price = parse_number(asset.get("current_price"))
        current_price = parse_number(merged.get("current_price"), asset_price)
        entry_price = parse_number(merged.get("entry_price") or merged.get("entry"), current_price)

        stop_loss = parse_number(merged.get("stop_loss"))
        stop_info = trailing_stops.get(symbol, {}) if isinstance(trailing_stops, dict) else {}
        trailing_stop = parse_number(stop_info.get("recommended_stop"))
        if trailing_stop is not None:
            stop_loss = max(stop_loss or -float("inf"), trailing_stop)
        if stop_loss is None:
            support = parse_number((asset.get("technicals") or {}).get("key_support"))
            if entry_price is not None and support is not None and support < entry_price:
                stop_loss = round(support * 0.97, 2)
            elif entry_price is not None:
                stop_loss = round(entry_price * 0.92, 2)

        target_12m = parse_number(merged.get("target_12m"))
        if target_12m is None and entry_price is not None:
            target_12m = round(entry_price * profile_target_multiplier(risk_profile), 2)

        if entry_price is None and current_price is not None:
            entry_price = current_price

        if entry_price is None:
            entry_price = 0.0

        if stop_loss is None:
            stop_loss = round(max(0.01, entry_price * 0.92), 2)

        if target_12m is None:
            target_12m = round(entry_price * profile_target_multiplier(risk_profile), 2)

        if entry_price > stop_loss:
            risk_reward = round((target_12m - entry_price) / (entry_price - stop_loss), 2)
        else:
            risk_reward = 2.0

        sector = infer_sector(asset, merged)

        thesis = merged.get("thesis") or merged.get("reasoning") or asset.get("reasoning") or f"{symbol} is selected by the strategy agent."
        thesis_invalidators = merged.get("thesis_invalidators")
        if not isinstance(thesis_invalidators, list):
            thesis_invalidators = ["Catalyst fails to materialize", "Trend or valuation thesis breaks"]

        thesis_status = str(merged.get("thesis_status") or "new").lower().strip()
        if thesis_status not in {"new", "active", "updated", "invalidated"}:
            thesis_status = "new"
        if held and thesis_status == "new":
            thesis_status = "active"

        financial_health = derive_financial_health(merged, asset)

        pick = {
            "rank": 0,
            "name": merged.get("name") or asset.get("name") or symbol,
            "symbol": symbol,
            "sector": sector,
            "confidence": round(clamp(confidence), 1),
            "risk_score": round(clamp(risk_score), 1),
            "risk_adjusted_score": risk_adjusted,
            "recommendation": rec,
            "reasoning": merged.get("reasoning") or asset.get("reasoning") or "",
            "position_size": normalize_position_size(merged.get("position_size"), risk_profile, len(normalized) + 1),
            "entry_price": round(entry_price, 2) if entry_price is not None else None,
            "stop_loss": round(stop_loss, 2) if stop_loss is not None else None,
            "target_12m": round(target_12m, 2) if target_12m is not None else None,
            "risk_reward_ratio": risk_reward,
            "thesis": thesis,
            "thesis_invalidators": thesis_invalidators,
            "thesis_status": thesis_status,
            "financial_health": financial_health,
            "key_news": merged.get("key_news") or asset.get("key_news") or [],
            "social_highlights": merged.get("social_highlights") or asset.get("social_highlights") or [],
            "technicals": merged.get("technicals") or asset.get("technicals") or {},
            "valuation": merged.get("valuation") or asset.get("valuation") or {},
            "fundamentals": merged.get("fundamentals") or asset.get("fundamentals") or {},
            "current_price": asset.get("current_price") or merged.get("current_price"),
            "watchlist": asset.get("watchlist"),
            "social_sentiment": asset.get("social_sentiment"),
            "social_buzz": asset.get("social_buzz"),
            "source_agreement": asset.get("source_agreement"),
        }

        if financial_health.get("altman_zone") == "distress":
            warnings.append(
                f"{symbol}: Altman Z={financial_health.get('altman_z')} (distress zone) — tighten risk controls or require an explicit turnaround thesis."
            )
        if isinstance(financial_health.get("piotroski"), (int, float)) and financial_health["piotroski"] <= 2:
            warnings.append(
                f"{symbol}: Piotroski F-Score={financial_health.get('piotroski')}/9 (weak fundamentals) — thesis needs extra confirmation."
            )

        normalized.append(pick)

    # Hard correlation limit: keep the strongest two names per group.
    grouped: dict[str, list[dict[str, Any]]] = {}
    for pick in normalized:
        symbol = str(pick.get("symbol") or "").upper()
        asset = asset_index.get(symbol, {})
        group = str(asset.get("watchlist") or pick.get("sector") or "other")
        grouped.setdefault(group, []).append(pick)

    final_picks: list[dict[str, Any]] = []
    for group, group_picks in grouped.items():
        ordered = sorted(group_picks, key=lambda p: (p.get("risk_adjusted_score") or 0, p.get("confidence") or 0), reverse=True)
        keep = ordered[:MAX_PICKS_PER_GROUP]
        cut = ordered[MAX_PICKS_PER_GROUP:]
        final_picks.extend(keep)
        if cut:
            kept_syms = ", ".join(p["symbol"] for p in keep)
            cut_syms = ", ".join(p["symbol"] for p in cut)
            warnings.append(f"{group}: max {MAX_PICKS_PER_GROUP} picks enforced — kept [{kept_syms}] cut [{cut_syms}].")

    final_picks = sorted(final_picks, key=lambda p: (p.get("risk_adjusted_score") or 0, p.get("confidence") or 0), reverse=True)
    for idx, pick in enumerate(final_picks, start=1):
        pick["rank"] = idx

    return final_picks, warnings


def fallback_strategy(sectors: dict[str, Any], risk_profile: str, market_context: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    macro = fallback_macro_environment(market_context)
    picks = fallback_picks(sectors, risk_profile, market_context)
    if not picks:
        raise RuntimeError("No picks available to build a fallback strategy")

    historical_accuracy = meta.get("accuracy_baseline")
    accuracy_path_str = meta.get("accuracy_path")
    if not historical_accuracy and accuracy_path_str:
        historical_accuracy = read_json(Path(accuracy_path_str), {})
    historical_accuracy = historical_accuracy or {}
    warnings = ["Strategy analysis unavailable — using deterministic fallback ranking."]

    return {
        "risk_profile": risk_profile,
        "macro_environment": macro,
        "portfolio_allocation": fallback_allocation(risk_profile),
        "cross_sector_insights": fallback_cross_sector_insights(market_context),
        "risk_adjusted_picks": picks,
        "priority_attention": [],
        "historical_accuracy": historical_accuracy,
        "warnings": warnings,
        "strategy_summary": "Fallback report generated because the strategy analysis was unavailable.",
    }


def run_write_report(report_data_path: Path, *, verbose: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "write_report.py"), str(report_data_path)],
        cwd=str(SKILL_DIR),
        text=True,
        capture_output=True,
        env=os.environ.copy(),
    )
    if verbose and proc.stdout:
        print(proc.stdout.rstrip())
    if proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "write_report.py failed")
    return proc


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble and write the final Tododeia report")
    parser.add_argument("--sectors", default=str(DEFAULT_OUT_DIR / "sectors.json"), help="Path to sectors JSON from pipeline.py")
    parser.add_argument("--strategy", required=True, help="Path to the MegaAgent strategy JSON, or - for stdin")
    parser.add_argument("--meta", default=str(DEFAULT_OUT_DIR / "pipeline_meta.json"), help="Path to pipeline_meta.json")
    parser.add_argument("--out-data", default=str(DEFAULT_OUT_DIR / "report_data.json"), help="Where to write the normalized REPORT_DATA JSON")
    parser.add_argument("--dry-run", action="store_true", help="Normalize and print JSON without calling write_report.py")
    parser.add_argument("--verbose", action="store_true", help="Print write_report.py output")
    args = parser.parse_args()

    strategy_raw = load_input(args.strategy)
    sectors = read_json(Path(args.sectors), {})
    meta = read_json(Path(args.meta), {})

    if not isinstance(strategy_raw, dict):
        raise RuntimeError("Strategy JSON must be an object")
    if not isinstance(sectors, dict) or not sectors:
        raise RuntimeError("Sectors JSON is missing or empty")

    risk_profile = normalize_risk_profile(strategy_raw.get("risk_profile") or meta.get("risk_profile"))
    market_context_path = Path(meta.get("market_context_path") or (DATA_DIR / "market_context.json"))
    market_context = read_json(market_context_path, {})
    accuracy_path_str = meta.get("accuracy_path")

    strategy = strategy_raw
    picks = strategy.get("risk_adjusted_picks")
    if not isinstance(picks, list) or not picks:
        strategy = fallback_strategy(sectors, risk_profile, market_context, meta)
        picks = strategy["risk_adjusted_picks"]

    normalized_picks, local_warnings = normalize_picks(picks, sectors, risk_profile, market_context)
    if not normalized_picks:
        strategy = fallback_strategy(sectors, risk_profile, market_context, meta)
        normalized_picks, local_warnings = normalize_picks(strategy["risk_adjusted_picks"], sectors, risk_profile, market_context)

    macro_environment = strategy.get("macro_environment") or fallback_macro_environment(market_context)
    portfolio_allocation = strategy.get("portfolio_allocation") or fallback_allocation(risk_profile)
    cross_sector_insights = strategy.get("cross_sector_insights") or fallback_cross_sector_insights(market_context)
    historical_accuracy = strategy.get("historical_accuracy") or meta.get("accuracy_baseline")
    if not historical_accuracy and accuracy_path_str:
        historical_accuracy = read_json(Path(accuracy_path_str), {})
    historical_accuracy = historical_accuracy or {}
    # Normalize short keys (1d/5d/30d) to window_* schema expected by the dashboard
    _acc_key_map = {"1d": "window_1d", "5d": "window_5d", "30d": "window_30d"}
    historical_accuracy = {_acc_key_map.get(k, k): v for k, v in historical_accuracy.items()}

    accuracy_notable = meta.get("accuracy_notable") or historical_accuracy.get("notable") or "No historical data available"
    thesis_notes = []
    for pick in normalized_picks[:5]:
        thesis_notes.append(f"{pick['symbol']}:{pick.get('thesis_status', 'new')}")
    if thesis_notes and "notable" in historical_accuracy:
        historical_accuracy["notable"] = f"{accuracy_notable} | Thesis status: {'; '.join(thesis_notes)}"
    elif thesis_notes:
        historical_accuracy["notable"] = f"{accuracy_notable} | Thesis status: {'; '.join(thesis_notes)}"
    else:
        historical_accuracy["notable"] = accuracy_notable

    warnings = []
    warnings.extend(strategy.get("warnings") or [])
    warnings.extend(local_warnings)
    warnings.extend(
        [
            f"Meta: strategy assembled from {meta.get('mega_context_chars', 'unknown')} compressed characters.",
        ]
    )
    priority_attention = strategy.get("priority_attention") or []
    if isinstance(priority_attention, list):
        for item in priority_attention:
            if isinstance(item, dict) and item.get("symbol") and item.get("reason"):
                warnings.append(f"{item['symbol']}: {item['reason']} — {item.get('action', 'review')}")

    report_data = {
        "brand": "Tododeia",
        "creator": "@quebert",
        "generated_at": now_utc(),
        "risk_profile": risk_profile,
        "executive_summary": strategy.get("strategy_summary") or strategy.get("executive_summary") or "Tododeia strategy summary unavailable.",
        "macro_environment": macro_environment,
        "portfolio_allocation": portfolio_allocation,
        "cross_sector_insights": cross_sector_insights,
        "risk_adjusted_picks": normalized_picks,
        "historical_accuracy": historical_accuracy,
        "warnings": warnings,
        "sectors": sectors,
        "spy_price_at_report": meta.get("spy_price_at_report") or (market_context.get("macro") or {}).get("spy_price"),
        "priority_attention": priority_attention,
        "strategy_summary": strategy.get("strategy_summary") or strategy.get("executive_summary"),
    }

    out_path = Path(args.out_data)
    write_json(out_path, report_data)

    if args.dry_run:
        print(json.dumps(report_data, indent=2, ensure_ascii=False))
        return

    run_write_report(out_path, verbose=args.verbose)

    print(f"[assemble_report] normalized report_data → {out_path}")
    print("[assemble_report] report written successfully")


if __name__ == "__main__":
    main()