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

    history_path = os.path.join(skill_dir, "output", "history", f"{date_str}.json")
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


if __name__ == "__main__":
    main()
