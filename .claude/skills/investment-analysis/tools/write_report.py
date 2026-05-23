#!/usr/bin/env python3
"""
write_report.py — Validates REPORT_DATA schema and writes both output files
(history + dashboard) using temp-then-rename so neither file is left in a
partial/inconsistent state if a write fails midway.

Usage:
    python3 tools/write_report.py <path_to_report_json>
    echo '<json>' | python3 tools/write_report.py -

Exit codes:
    0  — success
    1  — validation error or write failure (details on stderr)
"""

import json
import os
import sys
import tempfile
from datetime import datetime

# ---------------------------------------------------------------------------
# Schema requirements
# ---------------------------------------------------------------------------

REQUIRED_TOP = [
    "brand", "creator", "generated_at", "risk_profile",
    "executive_summary", "macro_environment", "portfolio_allocation",
    "cross_sector_insights", "risk_adjusted_picks", "historical_accuracy",
    "warnings", "sectors",
]

REQUIRED_MACRO = [
    "summary", "interest_rate_outlook", "inflation_outlook",
    "geopolitical_risk", "key_factors",
]

REQUIRED_PICK = [
    "rank", "name", "symbol", "sector", "confidence", "risk_score",
    "risk_adjusted_score", "recommendation", "reasoning", "position_size",
    "entry_price", "stop_loss", "target_12m", "risk_reward_ratio",
    "thesis", "thesis_invalidators", "thesis_status",
]


def validate(data: dict) -> list[str]:
    """Return a list of validation errors (empty = OK)."""
    errors = []

    # Top-level fields
    for field in REQUIRED_TOP:
        if field not in data:
            errors.append(f"Missing top-level field: '{field}'")

    if errors:
        return errors  # stop early — nested checks would produce noise

    # macro_environment
    macro = data.get("macro_environment", {})
    if not isinstance(macro, dict):
        errors.append("macro_environment must be an object")
    else:
        for field in REQUIRED_MACRO:
            if field not in macro:
                errors.append(f"Missing macro_environment.{field}")

    # risk_adjusted_picks
    picks = data.get("risk_adjusted_picks", [])
    if not isinstance(picks, list) or len(picks) == 0:
        errors.append("risk_adjusted_picks must be a non-empty array")
    else:
        for i, pick in enumerate(picks):
            symbol = pick.get("symbol", f"index {i}")
            for field in REQUIRED_PICK:
                if field not in pick:
                    errors.append(f"Pick '{symbol}' missing field: '{field}'")

    # sectors
    sectors = data.get("sectors", {})
    if not isinstance(sectors, dict) or len(sectors) == 0:
        errors.append("sectors must be a non-empty object")

    return errors


# ---------------------------------------------------------------------------
# Atomic write helpers
# ---------------------------------------------------------------------------

def _write_tmp(path: str, content: str) -> str:
    """Write content to a .tmp file beside path, return tmp path."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    dir_ = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return tmp


def write_both(history_path: str, report_path: str, serialized: str) -> None:
    """
    Write both files using temp-then-rename strategy:
      1. Write both to .tmp files (if either write fails, no target is touched)
      2. Rename both .tmp → final (os.replace is atomic on POSIX)
      3. On any failure, clean up .tmp files before raising

    This guarantees: either BOTH files are updated or NEITHER is.
    """
    tmp_history = tmp_report = None
    try:
        tmp_history = _write_tmp(history_path, serialized)
        tmp_report = _write_tmp(report_path, serialized)
        # Both temps written — now atomically promote
        os.replace(tmp_history, history_path)
        tmp_history = None  # owned by final path now
        os.replace(tmp_report, report_path)
        tmp_report = None
    except Exception:
        for tmp in [tmp_history, tmp_report]:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
        raise


# ---------------------------------------------------------------------------
# History pruning
# ---------------------------------------------------------------------------

def prune_history(history_dir: str, keep: int = 30) -> int:
    """Delete oldest history files beyond `keep`. Returns count deleted."""
    files = sorted(
        [f for f in os.listdir(history_dir) if f.endswith(".json")],
        reverse=True,
    )
    deleted = 0
    for old_file in files[keep:]:
        os.unlink(os.path.join(history_dir, old_file))
        deleted += 1
    return deleted


# ---------------------------------------------------------------------------
# Active positions carry-forward
# ---------------------------------------------------------------------------

_ACTIVE_STATUSES = {"active", "updated", "new"}


def update_active_positions(data: dict, date_str: str, skill_dir: str) -> None:
    """Merge today's picks into data/active_positions.json.

    - Adds/updates picks whose thesis_status is in {active, updated, new}
      and recommendation is not 'sell'.
    - Removes picks whose recommendation is 'sell' OR thesis_status is
      'invalidated'.
    - Preserves positions from prior sessions that were not in today's report
      (carry-forward: they remain until explicitly invalidated).
    """
    active_path = os.path.join(skill_dir, "data", "active_positions.json")

    # Load existing active positions (keyed by symbol)
    existing: dict = {}
    if os.path.exists(active_path):
        try:
            with open(active_path, encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            existing = {}

    picks = data.get("risk_adjusted_picks", [])
    for pick in picks:
        sym = pick.get("symbol")
        if not sym:
            continue
        status = pick.get("thesis_status", "new")
        rec = (pick.get("recommendation") or "").lower()

        if rec == "sell" or status == "invalidated":
            existing.pop(sym, None)
        elif status in _ACTIVE_STATUSES:
            existing[sym] = {
                "symbol": sym,
                "name": pick.get("name", sym),
                "entry_price": pick.get("entry_price"),
                "stop_loss": pick.get("stop_loss"),
                "target_12m": pick.get("target_12m"),
                "thesis": pick.get("thesis"),
                "thesis_status": status,
                "thesis_invalidators": pick.get("thesis_invalidators", []),
                "recommendation": rec,
                "position_size": pick.get("position_size"),
                "last_seen_date": date_str,
                "last_rank": pick.get("rank"),
            }

    try:
        os.makedirs(os.path.dirname(os.path.abspath(active_path)), exist_ok=True)
        with open(active_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        active_count = len(existing)
        print(f"OK  active   → {active_path}  ({active_count} position(s))")
    except OSError as exc:
        print(f"WARN: Could not write active_positions.json — {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Portfolio health summary (supplementary — not schema-validated)
# ---------------------------------------------------------------------------

def build_portfolio_health(skill_dir: str) -> dict | None:
    """Compute portfolio-level P&L and sector allocation from portfolio_market.json.

    This data is injected into the final report JSON as `portfolio_health`.
    It is computed in Python (not by the LLM) for accuracy.
    """
    # portfolio_market.json lives at project root data/, not in skill_dir/data/
    proj_root = os.path.dirname(os.path.dirname(os.path.dirname(skill_dir)))
    pm_path = os.path.join(proj_root, "data", "portfolio_market.json")
    if not os.path.exists(pm_path):
        return None
    try:
        with open(pm_path, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return None
    # Support both {"positions": [...]} dict and bare list formats
    if isinstance(raw, dict):
        positions = raw.get("positions") or []
        total_cost = raw.get("total_cost", 0) or 0
        total_value = raw.get("total_current_value", 0) or 0
        total_pnl_amount = total_value - total_cost
        total_pnl_pct = round(raw.get("total_pnl_pct", 0) or 0, 2)
    elif isinstance(raw, list):
        positions = raw
        total_cost = sum((p.get("cost_basis") or 0) for p in positions if isinstance(p, dict))
        total_value = sum(
            (p.get("current_price") or 0) * (p.get("quantity") or 0)
            for p in positions if isinstance(p, dict)
        )
        total_pnl_amount = total_value - total_cost
        total_pnl_pct = round((total_pnl_amount / total_cost * 100), 2) if total_cost else 0
    else:
        return None
    if not positions:
        return None

    sector_alloc: dict[str, float] = {}
    for p in positions:
        if not isinstance(p, dict):
            continue
        sec = p.get("sector", "other")
        val = (p.get("cost_basis") or 0) + (p.get("pnl_amount") or 0)
        sector_alloc[sec] = sector_alloc.get(sec, 0) + val

    sector_pct = {
        sec: round(val / total_value * 100, 1) if total_value else 0
        for sec, val in sorted(sector_alloc.items(), key=lambda x: -x[1])
    }

    # Top 5 performers and bottom 3 by P&L%
    valid = [p for p in positions if isinstance(p, dict) and p.get("symbol")]
    sorted_by_pnl = sorted(valid, key=lambda x: (x.get("pnl_pct") or 0), reverse=True)
    top_performers = [
        {"symbol": p["symbol"], "pnl_pct": round(p.get("pnl_pct") or 0, 2)}
        for p in sorted_by_pnl[:5]
    ]
    bottom_performers = [
        {"symbol": p["symbol"], "pnl_pct": round(p.get("pnl_pct") or 0, 2)}
        for p in sorted_by_pnl[-3:]
    ]

    return {
        "positions_count": len(valid),
        "total_cost_basis": round(total_cost, 2),
        "total_current_value": round(total_value, 2),
        "total_pnl_amount": round(total_pnl_amount, 2),
        "total_pnl_pct": total_pnl_pct,
        "sector_allocation_pct": sector_pct,
        "top_performers": top_performers,
        "bottom_performers": bottom_performers,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Read input
    if len(sys.argv) == 2 and sys.argv[1] == "-":
        raw = sys.stdin.read()
    elif len(sys.argv) == 2:
        with open(sys.argv[1], encoding="utf-8") as f:
            raw = f.read()
    else:
        print(
            "Usage: python3 tools/write_report.py <json_file>  OR  ... | python3 tools/write_report.py -",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON — {exc}", file=sys.stderr)
        sys.exit(1)

    # Validate schema
    errors = validate(data)
    if errors:
        print(f"ERROR: Schema validation failed ({len(errors)} issue(s)):", file=sys.stderr)
        for err in errors:
            print(f"  • {err}", file=sys.stderr)
        sys.exit(1)

    # Resolve output paths relative to skill root (parent of tools/)
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    date_str = datetime.now().strftime("%Y-%m-%d")

    # If a history file for today already exists (e.g. a second run the same day),
    # use an HHmm suffix so both runs are preserved for accuracy tracking.
    # parse_date() strips any suffix after the first 10 chars, so windows still work.
    history_dir_path = os.path.join(skill_dir, "output", "history")
    base_history = os.path.join(history_dir_path, f"{date_str}.json")
    if os.path.exists(base_history):
        time_suffix = datetime.now().strftime("%H%M")
        history_path = os.path.join(history_dir_path, f"{date_str}-{time_suffix}.json")
    else:
        history_path = base_history
    report_path = os.path.join(skill_dir, "dashboard", "public", "data", "report.json")

    serialized = json.dumps(data, indent=2, ensure_ascii=False)

    # Write both atomically
    try:
        write_both(history_path, report_path, serialized)
    except Exception as exc:
        print(f"ERROR: Write failed — {exc}", file=sys.stderr)
        sys.exit(1)

    # Prune history
    history_dir = os.path.dirname(history_path)
    pruned = prune_history(history_dir)

    print(f"OK  history  → {history_path}")
    print(f"OK  report   → {report_path}")
    if pruned:
        print(f"    Pruned {pruned} old history file(s)")

    # Persist active positions for carry-forward injection in next run
    update_active_positions(data, date_str, skill_dir)

    # Enrich report with portfolio health summary (computed from portfolio_market.json)
    health = build_portfolio_health(skill_dir)
    if health:
        data["portfolio_health"] = health
        serialized = json.dumps(data, indent=2, ensure_ascii=False)
        # Overwrite both files with the enriched data
        try:
            write_both(history_path, report_path, serialized)
        except Exception as exc:
            print(f"WARN: portfolio_health re-write failed — {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
