#!/usr/bin/env python3
"""
accuracy_windows.py — Computa accuracy multi-ventana (1d / 5d / 30d) para Tododeia.

Compara los picks de sesiones anteriores contra los precios actuales, calculando
retorno absoluto y alpha vs SPY para cada ventana temporal.

Usage:
    python3 tools/accuracy_windows.py
    python3 tools/accuracy_windows.py --out /tmp/accuracy.json

Output: JSON a stdout (o --out FILE) con estructura:
{
  "window_1d":  { "source_date": "YYYY-MM-DD", "calls_made": N, "calls_correct": M, "accuracy_pct": X, "beat_spy": K, "alpha_avg": F, "picks": [...] },
  "window_5d":  { ... },
  "window_30d": { ... }
}
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
HISTORY_DIR = SKILL_DIR / "output" / "history"
MARKET_CTX  = SKILL_DIR / "data" / "market_context.json"

# Aproximaciones en días de calendario
WINDOW_CALENDAR_DAYS = {
    "1d":  2,    # ayer (1-2 días naturales para cubrir fines de semana)
    "5d":  8,    # ~5 días hábiles ≈ 1 semana natural
    "30d": 35,   # ~22 días hábiles ≈ 30-35 días naturales
}


def load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_date(filename: str) -> date | None:
    """Extrae la fecha del nombre del archivo, ej. '2026-05-21.json' → date(2026,5,21).
    Ignora sufijos como '-pm': '2026-04-12-pm.json' → date(2026,4,12)."""
    stem = Path(filename).stem  # sin .json
    # Tomar solo los primeros 10 chars YYYY-MM-DD
    date_part = stem[:10]
    try:
        return datetime.strptime(date_part, "%Y-%m-%d").date()
    except ValueError:
        return None


def get_history_files() -> list[tuple[date, Path]]:
    """Devuelve lista de (fecha, path) ordenada de más reciente a más antigua."""
    files = []
    for f in HISTORY_DIR.glob("*.json"):
        d = parse_date(f.name)
        if d:
            files.append((d, f))
    files.sort(key=lambda x: x[0], reverse=True)
    return files


def find_file_for_window(history_files: list[tuple[date, Path]], today: date, window_key: str) -> tuple[date, Path] | None:
    """Encuentra el archivo más cercano a (today - WINDOW_CALENDAR_DAYS[window_key]).
    Excluye el archivo de hoy (índice 0)."""
    target_date = today - timedelta(days=WINDOW_CALENDAR_DAYS[window_key])
    # Excluir el archivo de hoy
    candidates = [(d, p) for d, p in history_files if d < today]
    if not candidates:
        return None
    # Encontrar el más cercano al target (puede ser antes o después del target)
    best = min(candidates, key=lambda x: abs((x[0] - target_date).days))
    return best


def get_current_prices(mkt: dict) -> dict[str, float]:
    """Construye un dict {symbol: price} de market_context.json.
    Incluye prices_snapshot y candidates como fuentes."""
    prices: dict[str, float] = {}
    # Fuente 1: prices_snapshot
    for sym, data in mkt.get("prices_snapshot", {}).items():
        if isinstance(data, dict) and data.get("price"):
            prices[sym] = float(data["price"])
        elif isinstance(data, (int, float)):
            prices[sym] = float(data)
    # Fuente 2: candidates (complementario, usa price_at_fetch)
    for c in mkt.get("candidates", []):
        sym = c.get("symbol")
        price = c.get("price_at_fetch") or c.get("price")
        if sym and price and sym not in prices:
            prices[sym] = float(price)
    return prices


def fetch_missing_prices(symbols: list[str], existing: dict[str, float]) -> dict[str, float]:
    """Busca precios actuales en yfinance para símbolos no en el snapshot."""
    missing = [s for s in symbols if s not in existing]
    if not missing:
        return existing
    try:
        import yfinance as yf
        result = dict(existing)
        tickers = yf.Tickers(" ".join(missing))
        for sym in missing:
            try:
                info = tickers.tickers[sym].fast_info
                price = getattr(info, "last_price", None)
                if price:
                    result[sym] = float(price)
            except Exception:
                pass
        return result
    except ImportError:
        print("[accuracy_windows] yfinance not available, skipping missing prices", file=sys.stderr)
        return existing


def compute_window(
    source_date: date,
    source_file: Path,
    current_prices: dict[str, float],
    today_spy: float,
) -> dict:
    """Calcula el accuracy de los picks de source_file contra current_prices."""
    h = load_json(source_file)
    picks_raw = h.get("risk_adjusted_picks", h.get("picks", []))
    spy_then = h.get("spy_price_at_report")

    spy_return = (today_spy - spy_then) / spy_then if spy_then and today_spy else None

    picks_out = []
    for p in picks_raw:
        if not isinstance(p, dict):
            continue
        sym = p.get("symbol")
        entry = p.get("entry_price") or p.get("entry")
        rec = p.get("recommendation", "?")
        status = p.get("thesis_status", "new")

        if not sym or not entry:
            continue

        now = current_prices.get(sym)
        if not now:
            continue

        pick_return = (now - entry) / entry
        # Correct = price direction matches recommendation
        if rec in ("buy", "strong buy"):
            correct = pick_return > 0
        elif rec in ("sell", "strong sell"):
            correct = pick_return < 0
        else:  # hold — count as neutral / skip from wins
            correct = None

        alpha = (pick_return - spy_return) if spy_return is not None else None
        beat_spy = (alpha > 0) if alpha is not None else None

        # Outlier filter — return > ±85% almost certainly indicates bad entry data
        # (e.g. pre-split vs post-split price mismatch, crypto stale price, typo)
        is_outlier = abs(pick_return * 100) > 85

        picks_out.append({
            "symbol": sym,
            "entry": round(entry, 2),
            "now": round(now, 2),
            "return_pct": round(pick_return * 100, 1),
            "alpha_pct": round(alpha * 100, 1) if alpha is not None else None,
            "rec": rec,
            "correct": correct if not is_outlier else None,  # exclude outliers from accuracy
            "beat_spy": beat_spy if not is_outlier else None,
            "thesis_status": status,
        })
        if is_outlier:
            picks_out[-1]["outlier"] = True


    # Metrics — only count buy/sell calls (not hold, not outliers) for accuracy
    actionable = [p for p in picks_out if p["correct"] is not None]
    calls_correct = sum(1 for p in actionable if p["correct"])
    beat_spy_count = sum(1 for p in picks_out if p["beat_spy"])
    alpha_vals = [p["alpha_pct"] for p in picks_out if p["alpha_pct"] is not None]
    avg_alpha = round(sum(alpha_vals) / len(alpha_vals), 1) if alpha_vals else None

    # Best and worst picks
    sorted_picks = sorted(picks_out, key=lambda x: x["return_pct"], reverse=True)
    best = sorted_picks[0] if sorted_picks else None
    worst = sorted_picks[-1] if sorted_picks else None

    return {
        "source_date": source_date.isoformat(),
        "calls_made": len(actionable),
        "calls_correct": calls_correct,
        "accuracy_pct": round(calls_correct / len(actionable) * 100) if actionable else None,
        "total_picks": len(picks_out),
        "beat_spy": beat_spy_count,
        "beat_spy_pct": round(beat_spy_count / len(picks_out) * 100) if picks_out else None,
        "alpha_avg_pct": avg_alpha,
        "spy_return_pct": round(spy_return * 100, 2) if spy_return is not None else None,
        "best_pick": f"{best['symbol']} {best['return_pct']:+.1f}%" if best else None,
        "worst_pick": f"{worst['symbol']} {worst['return_pct']:+.1f}%" if worst else None,
        "picks": picks_out,
    }


def build_notable_summary(windows: dict) -> str:
    """Genera la frase 'notable' de 1 línea para el MegaAgent."""
    parts = []
    for name, w in windows.items():
        if w is None:
            continue
        pct = w.get("accuracy_pct")
        spy_beat = w.get("beat_spy")
        total = w.get("total_picks", 0)
        src = w.get("source_date", "?")
        if pct is not None:
            parts.append(f"{name}: {pct}% ({spy_beat}/{total} beat SPY, from {src})")
    return " | ".join(parts) if parts else "No historical data available"


def main():
    parser = argparse.ArgumentParser(description="Multi-window accuracy tracker for Tododeia")
    parser.add_argument("--out", default=None, help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    # Load today's market context
    mkt = load_json(MARKET_CTX)
    if not mkt:
        print("[accuracy_windows] ERROR: data/market_context.json not found — run pre_fetch.py first", file=sys.stderr)
        sys.exit(1)

    today = date.today()
    today_spy = mkt.get("macro", {}).get("spy_price")
    base_prices = get_current_prices(mkt)

    # Get all history files
    history_files = get_history_files()
    if not history_files:
        print("[accuracy_windows] No history files found in output/history/", file=sys.stderr)
        sys.exit(1)

    # Find the file for each window
    window_files: dict[str, tuple[date, Path] | None] = {}
    for wk in ("1d", "5d", "30d"):
        result = find_file_for_window(history_files, today, wk)
        window_files[wk] = result
        if result:
            print(f"[accuracy_windows] Window {wk}: using {result[1].name} ({result[0]})", file=sys.stderr)
        else:
            print(f"[accuracy_windows] Window {wk}: no suitable file found", file=sys.stderr)

    # Collect all symbols across all windows to batch-fetch missing prices
    all_symbols: set[str] = set()
    for wk, wf in window_files.items():
        if wf:
            h = load_json(wf[1])
            for p in h.get("risk_adjusted_picks", h.get("picks", [])):
                if isinstance(p, dict) and p.get("symbol"):
                    all_symbols.add(p["symbol"])
    current_prices = fetch_missing_prices(list(all_symbols), base_prices)

    # Compute each window
    results: dict[str, dict | None] = {}
    for wk, wf in window_files.items():
        if wf:
            results[wk] = compute_window(wf[0], wf[1], current_prices, today_spy)
        else:
            results[wk] = None

    # Add a single-line summary for the MegaAgent
    results["notable"] = build_notable_summary(
        {k: v for k, v in results.items() if isinstance(v, dict)}
    )
    results["computed_at"] = today.isoformat()
    results["today_spy"] = today_spy

    output = json.dumps(results, indent=2)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"[accuracy_windows] Written to {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
