#!/usr/bin/env python3
"""Start the report UI locally.

Primary path:
  - if dashboard/package.json exists, ensure dependencies are installed and
    start the Next.js dashboard on the requested port.

Fallback path:
  - if the dashboard is unavailable, render a simple legacy HTML preview from
    dashboard/public/data/report.json into output/report.html and serve output/
    with Python's built-in HTTP server.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import socket
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = SKILL_DIR / "output"
DASHBOARD_DIR = SKILL_DIR / "dashboard"
DEFAULT_PORT = 3420


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def ensure_node_modules() -> bool:
    if not (DASHBOARD_DIR / "package.json").exists():
        return False
    if (DASHBOARD_DIR / "node_modules").exists():
        return True

    print("[serve_report] Installing dashboard dependencies…")
    proc = subprocess.run(
        ["npm", "install", "--prefix", str(DASHBOARD_DIR)],
        cwd=str(SKILL_DIR),
        text=True,
    )
    return proc.returncode == 0


def render_legacy_preview(port: int) -> Path:
    report_path = DASHBOARD_DIR / "public" / "data" / "report.json"
    out_html = OUTPUT_DIR / "report.html"
    report = {}
    if report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            report = {}

    title = html_lib.escape(str(report.get("executive_summary") or "Tododeia Report Preview"))
    picks = report.get("risk_adjusted_picks") or []
    pick_rows = "\n".join(
      f"<tr><td>{i + 1}</td><td>{html_lib.escape(str(p.get('symbol', '')))}</td><td>{html_lib.escape(str(p.get('name', '')))}</td><td>{html_lib.escape(str(p.get('recommendation', '')))}</td><td>{html_lib.escape(str(p.get('risk_adjusted_score', '')))}</td></tr>"
        for i, p in enumerate(picks)
        if isinstance(p, dict)
    ) or "<tr><td colspan='5'>No picks available</td></tr>"

    report_json = html_lib.escape(json.dumps(report, indent=2, ensure_ascii=False))

    preview_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tododeia Report Preview</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 0; padding: 24px; background: #0b1020; color: #e5e7eb; }}
    .card {{ background: #111827; border: 1px solid #243047; border-radius: 16px; padding: 20px; margin-bottom: 20px; }}
    h1, h2 {{ margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid #243047; }}
    .muted {{ color: #9ca3af; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Tododeia Report Preview</h1>
    <p class="muted">Fallback preview generated because the dashboard package was not available.</p>
    <p>{title}</p>
  </div>
  <div class="card">
    <h2>Top Picks</h2>
    <table>
      <thead><tr><th>#</th><th>Symbol</th><th>Name</th><th>Recommendation</th><th>Score</th></tr></thead>
      <tbody>
        {pick_rows}
      </tbody>
    </table>
  </div>
  <div class="card">
    <h2>Report JSON</h2>
    <pre style="white-space: pre-wrap; word-break: break-word;">{report_json}</pre>
  </div>
</body>
</html>"""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_html.write_text(preview_html, encoding="utf-8")
    return out_html


def start_next_dashboard(port: int) -> None:
    if port_in_use(port):
        print(f"[serve_report] Port {port} already in use — dashboard is likely running.")
        print(f"[serve_report] Open: http://localhost:{port}")
        return

    if not ensure_node_modules():
        print("[serve_report] dashboard package unavailable; falling back to static preview")
        render_legacy_preview(port)
        subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port), "--directory", str(OUTPUT_DIR)],
            cwd=str(SKILL_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print(f"[serve_report] Open: http://localhost:{port}/report.html")
        return

    log_path = OUTPUT_DIR / "dashboard.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log_file:
        subprocess.Popen(
            ["npm", "run", "dev", "--prefix", str(DASHBOARD_DIR), "--", "-p", str(port)],
            cwd=str(SKILL_DIR),
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )
    print(f"[serve_report] Starting dashboard on http://localhost:{port}")
    print(f"[serve_report] Log: {log_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Tododeia report locally")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    start_next_dashboard(args.port)


if __name__ == "__main__":
    main()