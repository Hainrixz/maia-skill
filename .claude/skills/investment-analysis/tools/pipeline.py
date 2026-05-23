#!/usr/bin/env python3
"""Local deterministic pre-processing pipeline for Tododeia.

This script absorbs the mechanical work that used to live inside the MegaAgent
orchestrator:

- run pre_fetch.py for the full watchlist universe
- run news_fetch.py and sec_risk_fetch.py in parallel
- compute accuracy windows
- build sectors JSON
- update trailing stops when prior history exists
- compress all context into a single MegaAgent input block
- write pipeline_meta.json for the strategy step

The only remaining LLM work is the strategy synthesis step.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SKILL_DIR.parent.parent.parent
DATA_DIR = SKILL_DIR / "data"
HISTORY_DIR = SKILL_DIR / "output" / "history"
DEFAULT_OUT_DIR = Path("/tmp/tododeia")


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_history_date(path: Path) -> date | None:
    stem = path.stem[:10]
    try:
        return datetime.strptime(stem, "%Y-%m-%d").date()
    except ValueError:
        return None


def find_latest_history_file() -> Path | None:
    if not HISTORY_DIR.exists():
        return None

    candidates: list[Path] = []
    for path in HISTORY_DIR.glob("*.json"):
        if parse_history_date(path):
            candidates.append(path)

    if not candidates:
        return None

    def sort_key(path: Path) -> tuple[date, float, str]:
        parsed = parse_history_date(path) or date.min
        mtime = path.stat().st_mtime if path.exists() else 0.0
        return (parsed, mtime, path.name)

    return max(candidates, key=sort_key)


def tail(text: str | None, limit: int = 30) -> str:
    if not text:
        return ""
    lines = text.strip().splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    return "\n".join(lines[-limit:])


def run_command(
    label: str,
    command: list[str],
    *,
    cwd: Path = SKILL_DIR,
    verbose: bool = False,
    allow_failure: bool = False,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        env=os.environ.copy(),
    )

    if verbose and proc.stdout:
        print(proc.stdout.rstrip())
    if verbose and proc.stderr:
        print(proc.stderr.rstrip(), file=sys.stderr)

    if proc.returncode != 0:
        print(f"[pipeline] {label}: failed ({proc.returncode})", file=sys.stderr)
        if not verbose:
            if proc.stdout:
                print(tail(proc.stdout), file=sys.stderr)
            if proc.stderr:
                print(tail(proc.stderr), file=sys.stderr)
        if not allow_failure:
            raise RuntimeError(f"{label} failed with exit code {proc.returncode}")
    else:
        print(f"[pipeline] {label}: ok")

    return proc


def run_parallel_fetches(
    tasks: dict[str, list[str]],
    *,
    verbose: bool = False,
) -> dict[str, subprocess.CompletedProcess[str]]:
    results: dict[str, subprocess.CompletedProcess[str]] = {}

    with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        futures = {
            pool.submit(run_command, label, command, verbose=verbose, allow_failure=True): label
            for label, command in tasks.items()
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                results[label] = future.result()
            except Exception as exc:
                failed = subprocess.CompletedProcess(args=tasks[label], returncode=1, stdout="", stderr=str(exc))
                results[label] = failed
                print(f"[pipeline] {label}: failed ({exc})", file=sys.stderr)

    return results


def build_accuracy_fallback(mkt: dict[str, Any]) -> dict[str, Any]:
    today_spy = (mkt.get("macro") or {}).get("spy_price")
    today = datetime.now(timezone.utc).date().isoformat()
    return {
        "window_1d": None,
        "window_5d": None,
        "window_30d": None,
        "notable": "No historical data available",
        "computed_at": today,
        "today_spy": today_spy,
        "source": "fallback",
    }


def summarize_processes(processes: dict[str, subprocess.CompletedProcess[str]]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for label, proc in processes.items():
        summary[label] = {
            "returncode": proc.returncode,
            "stdout_tail": tail(proc.stdout, 10),
            "stderr_tail": tail(proc.stderr, 10),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Tododeia's deterministic pre-processing pipeline")
    parser.add_argument("--risk-profile", default="moderate", help="Risk profile for metadata")
    parser.add_argument(
        "--watchlist",
        nargs="+",
        default=["all"],
        help="Watchlist names or tickers to pass through to pre_fetch.py (default: all)",
    )
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for temp pipeline artifacts")
    parser.add_argument("--news-top", type=int, default=12, help="Top N candidates to send to news_fetch.py")
    parser.add_argument("--sec-top", type=int, default=12, help="Top N candidates to send to sec_risk_fetch.py")
    parser.add_argument("--verbose", action="store_true", help="Print full subprocess output")
    args = parser.parse_args()

    risk_profile = normalize_risk_profile(args.risk_profile)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pre_fetch_cmd = [sys.executable, str(TOOLS_DIR / "pre_fetch.py"), "--watchlist", *args.watchlist]
    news_cmd = [sys.executable, str(TOOLS_DIR / "news_fetch.py"), "--top", str(args.news_top)]
    sec_cmd = [sys.executable, str(TOOLS_DIR / "sec_risk_fetch.py"), "--top", str(args.sec_top)]
    accuracy_path = out_dir / "accuracy.json"
    sectors_path = out_dir / "sectors.json"
    mega_context_path = out_dir / "mega_context.txt"
    pipeline_meta_path = out_dir / "pipeline_meta.json"

    print(f"[pipeline] start {now_utc()} | risk_profile={risk_profile} | watchlist={'+'.join(args.watchlist)}")

    # Step 1 — pre-fetch is critical
    run_command("pre_fetch", pre_fetch_cmd, verbose=args.verbose)

    market_context_path = DATA_DIR / "market_context.json"
    market_context = read_json(market_context_path)
    if not market_context:
        raise RuntimeError(f"market_context.json missing or empty after pre_fetch: {market_context_path}")

    latest_history = find_latest_history_file()

    # Step 2 — fetch news + SEC risks in parallel
    parallel_results = run_parallel_fetches({"news_fetch": news_cmd, "sec_risk_fetch": sec_cmd}, verbose=args.verbose)

    # Step 3 — accuracy windows (fallback when no history yet)
    accuracy_proc = run_command(
        "accuracy_windows",
        [sys.executable, str(TOOLS_DIR / "accuracy_windows.py"), "--out", str(accuracy_path)],
        verbose=args.verbose,
        allow_failure=True,
    )
    if accuracy_proc.returncode != 0 or not accuracy_path.exists():
        fallback = build_accuracy_fallback(market_context)
        write_json(accuracy_path, fallback)
        accuracy = fallback
        accuracy_note = "fallback"
        print("[pipeline] accuracy_windows: fallback written")
    else:
        accuracy = read_json(accuracy_path, build_accuracy_fallback(market_context))
        accuracy_note = "computed"

    # Step 4 — sectors are deterministic and rely on pre-fetched data only
    run_command(
        "build_sectors",
        [sys.executable, str(TOOLS_DIR / "build_sectors.py"), "--out", str(sectors_path)],
        verbose=args.verbose,
    )

    # Step 5 — trailing stops are useful only once we have prior history
    trailing_stops_path = DATA_DIR / "trailing_stops.json"
    update_stops_summary: dict[str, Any] = {"skipped": True, "reason": "no prior history"}
    if latest_history is not None:
        update_proc = run_command(
            "update_stops",
            [sys.executable, str(TOOLS_DIR / "update_stops.py"), "--history", str(latest_history)],
            verbose=args.verbose,
            allow_failure=True,
        )
        update_stops_summary = {
            "skipped": False,
            "returncode": update_proc.returncode,
            "history_file": latest_history.name,
            "written": trailing_stops_path.exists(),
        }
    else:
        print("[pipeline] update_stops: skipped (no prior history)")

    # Step 6 — compress all context into a single compact prompt block
    compress_cmd = [sys.executable, str(TOOLS_DIR / "compress_context.py")]
    if latest_history is not None:
        compress_cmd.extend(["--prev", str(latest_history)])
    compress_cmd.extend(["--out", str(mega_context_path)])
    run_command("compress_context", compress_cmd, verbose=args.verbose)

    mega_context_text = mega_context_path.read_text(encoding="utf-8") if mega_context_path.exists() else ""
    mega_context_chars = len(mega_context_text)

    if mega_context_chars > 6000:
        print(f"[pipeline] WARN mega_context exceeds guardrail: {mega_context_chars} chars", file=sys.stderr)

    meta = {
        "generated_at": now_utc(),
        "risk_profile": risk_profile,
        "watchlist": args.watchlist,
        "skill_dir": str(SKILL_DIR),
        "project_root": str(PROJECT_ROOT),
        "out_dir": str(out_dir),
        "market_context_path": str(market_context_path),
        "news_context_path": str(DATA_DIR / "news_context.json"),
        "sec_risk_context_path": str(DATA_DIR / "sec_risk_context.json"),
        "accuracy_path": str(accuracy_path),
        "sectors_path": str(sectors_path),
        "mega_context_path": str(mega_context_path),
        "mega_context_chars": mega_context_chars,
        "mega_context_guardrail_ok": mega_context_chars <= 6000,
        "accuracy_note": accuracy_note,
        "accuracy_baseline": accuracy,
        "accuracy_notable": accuracy.get("notable", "No historical data available"),
        "spy_price_at_report": (market_context.get("macro") or {}).get("spy_price"),
        "latest_history_path": str(latest_history) if latest_history else None,
        "latest_history_date": latest_history.stem[:10] if latest_history else None,
        "trailing_stops_path": str(trailing_stops_path),
        "parallel_fetches": summarize_processes(parallel_results),
        "update_stops": update_stops_summary,
        "correlation_warnings": market_context.get("correlation_warnings", []),
    }

    write_json(pipeline_meta_path, meta)

    print(f"[pipeline] accuracy → {accuracy_path}")
    print(f"[pipeline] sectors → {sectors_path}")
    print(f"[pipeline] mega_context → {mega_context_path} ({mega_context_chars} chars)")
    print(f"[pipeline] meta → {pipeline_meta_path}")


if __name__ == "__main__":
    main()