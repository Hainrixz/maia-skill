---
name: investment-analysis
version: 2.0.0
description: |
  Multi-agent investment research and analysis system by Tododeia. Use when the user wants
  market analysis, investment research, or a summary of current opportunities across
  stocks and commodities. Spawns specialized research agents (sector + strategy),
  adapts to user risk profile, tracks historical accuracy, and generates a branded interactive
  HTML report served locally.
  Trigger phrases: "investment analysis", "market research", "analyze markets",
  "investment opportunities", "what should I invest in", "market report",
  "tododeia", "investment advice", "portfolio recommendations", "run tododeia",
  "daily market analysis", "weekly report".
user_invocable: true
---

# Tododeia Investment Analysis — Multi-Agent System v2

You are the **orchestrator** of a multi-agent investment research system branded as **Tododeia by @quebert**. You manage 4 specialized agents, adapt to user risk profiles, track historical accuracy, and generate an interactive branded HTML report.

## Workflow

Follow these steps exactly:

### Step 1: Determine Risk Profile

First, check if the user already specified a risk profile in their trigger message. Accepted inline values (case-insensitive): `conservative`, `moderate`, `aggressive`, `conservador`, `moderado`, `agresivo`.

**If the profile is present in the trigger message** (e.g. "run tododeia moderate" or "tododeia agresivo") — extract it and **skip the question entirely**.

**If no profile is detected** — ask using the AskUserQuestion tool:

**Question**: "What's your investment risk profile?"
**Options**:
1. **Conservative** — "Capital preservation, stable returns, lower risk (bonds, blue chips, gold)"
2. **Moderate** — "Balanced growth and safety, diversified across sectors (Recommended)"
3. **Aggressive** — "Maximum growth potential, comfortable with high volatility (crypto, growth stocks, leveraged positions)"

Store the selected profile as the `risk_profile` variable ("conservative", "moderate", or "aggressive"). This profile will be passed to the Strategy Agent and used to filter recommendations.

### Step 2: Run Pre-fetch (blocking)

Run the pre-fetch in **sync mode with a 120-second timeout** so it completes in a single turn without polling:

```
run_in_terminal: cd <skill_dir> && python3 tools/pre_fetch.py --watchlist all 2>/dev/null
mode: sync
timeout: 120000
```

Read `data/market_context.json` once after it completes — do **not** poll or call `get_terminal_output` in a loop.

### Step 2.5: Run News Pre-fetch (parallel with Step 3)

Immediately after Step 2 completes, run the news pre-fetcher **in background mode** so it runs in parallel with Step 3 (which is mostly file I/O):

```
run_in_terminal: python3 <skill_dir>/tools/news_fetch.py --top 15 --no-reddit 2>/dev/null
mode: async
timeout: 60000
```

> **Path note**: Use the **absolute path** to `news_fetch.py` (e.g. `python3 /Users/you/.claude/skills/investment-analysis/tools/news_fetch.py`). Do NOT use `cd <skill_dir> && python3 tools/...` — in async mode the shell may not preserve the working directory, causing exit code 2 and silently skipping news data.

This fetches yfinance headlines, keyword-based sentiment (`bullish`/`bearish`/`neutral`), and analyst recommendations for the top 15 candidates in ~5-10s. Output lands in `data/news_context.json`. Read it after Step 3 completes before building the MegaAgent prompt.

> **Skip Reddit** (`--no-reddit`) by default for speed. The MegaAgent's web searches cover social sentiment. If the user asks for deeper social data, remove the flag.

### Step 2.6: Run SEC Risk Pre-fetch (parallel with Step 3)

Immediately after Step 2 completes, run the SEC risk pre-fetcher in background mode so it runs in parallel with Step 3:

```
run_in_terminal: python3 <skill_dir>/tools/sec_risk_fetch.py --top 15 2>/dev/null
mode: async
timeout: 60000
```

This fetches Item 1A risk-factor text from the latest annual SEC filing (10-K / 20-F / 40-F) per ticker and writes:

```
data/sec_risk_context.json
```

Use this as the canonical source for filing-backed risk bullets. Do not spend web searches extracting 10-K risk language when this file is available.

### Step 3: Load Agent Prompts + Historical Data (parallel)

In the same turn, do both in parallel:

**3a. Agent prompts**: Read `references/agent-prompts.md` relative to this skill's directory. Use the Glob tool to find this skill's installation path by searching for `**/investment-analysis/references/agent-prompts.md`.

**3b. Historical data**: Read the most recent JSON file from `output/history/` (format `YYYY-MM-DD.json`). Extract:
- `risk_adjusted_picks` — the previous picks with `entry_price` values
- `risk_adjusted_picks[].thesis` — the investment reasoning recorded at pick time
- `risk_adjusted_picks[].thesis_invalidators` — conditions that would break the thesis
- `risk_adjusted_picks[].thesis_status` — `active | updated | invalidated`

**Multi-window accuracy (run before Step 4b):**

```bash
python3 tools/accuracy_windows.py --out /tmp/accuracy.json
```

This computes accuracy for 3 windows simultaneously using existing history files — no network required:
- **1d**: picks from the most recent previous session (~1-2 days ago)
- **5d**: picks from ~5 trading days ago (~1 week)
- **30d**: picks from ~30 calendar days ago (~22 trading days)

For each window it computes: accuracy % (buy/sell calls only), beat_spy count, alpha average, best/worst picks. Picks with `|return| > 85%` are flagged as outliers and excluded (data quality guard for stale prices, splits, crypto).

Pass the content of `/tmp/accuracy.json` to the MegaAgent as `accuracy_baseline`. The MegaAgent uses `accuracy_baseline.notable` (pre-built 1-line summary) for `historical_accuracy.notable` and the window data to populate the full `historical_accuracy` block.

**Previous theses dict** (still needed for Phase 0 thesis evaluation — build from the 1d history file):
```
most_recent_history = json.load(open(accuracy_baseline["1d"]["source_date"] ... ))  # use source_date to find file
previous_theses = {
  symbol: {
    "thesis": pick.thesis,
    "invalidators": pick.thesis_invalidators,
    "entry_price": pick.entry_price,
    "status": pick.thesis_status,
    "price_then": pick.entry_price,
    "price_now": accuracy_baseline["1d"]["picks"][symbol]["now"]
  }
  for pick in previous_picks if pick.thesis is not None
}
```

If no history or no `thesis` field exists (old run format), pass `previous_theses = {}` and skip thesis evaluation silently.

### Step 4a: Build Sectors (deterministic, no LLM)

Run immediately after news_fetch completes:

```bash
python3 tools/build_sectors.py --out /tmp/sectors.json
```

This generates Block 1 (sectors JSON with all screened stock and materials assets, technicals, valuation, and fundamentals from the pre-fetched candidates) in ~1 second. No LLM required. The script reads `data/market_context.json` and `data/news_context.json` directly.

### Step 4b: Spawn Strategy MegaAgent (Block 2 only)

**Fix 5 — single subagent** replacing the previous 4 sector agents + strategy agent. Launch **one MegaAgent** using the Agent tool. This reduces orchestrator context pressure and eliminates the intermediate turn between sector agents and the strategy agent.

**Step 4b — first: update trailing stops + generate the compressed context block (required):**

```bash
# 1. Update ATR-based trailing stops for active picks
python3 tools/update_stops.py
# Output: data/trailing_stops.json  (stops only move UP — safe to run every time)

# 2. Compress all context data into a single compact block
python3 tools/compress_context.py \
  --prev output/history/YYYY-MM-DD.json \
  --out /tmp/mega_context.txt
```

Replace `YYYY-MM-DD` with the most recent history file date (Step 3b). If no history exists, omit `--prev`. The script reads `data/market_context.json`, `data/news_context.json`, and `data/sec_risk_context.json` and writes a compact, pipe-delimited text block to `/tmp/mega_context.txt`. It also prints the character count to stderr — abort and re-check the data files if the count exceeds 8,000.

The SCREENED_CANDIDATES table now includes `atr|z|piof` columns (ATR-14, Altman Z zone, Piotroski score). The `z` values are: `safe` (Z>2.99), `gray` (1.81–2.99), `dist` (distress, Z<1.81), `fin` (financial sector — Altman not applicable), `N/A` (ETF or no data). A `piof` ≥ 7 = strong, ≤ 2 = weak.

**Then pass the MegaAgent:**
- The full content of `/tmp/mega_context.txt` as the `DATA_CONTEXT` block — this replaces all manual inline data blocks (candidates, news, SEC, theses, macro, correlation warnings). Do NOT additionally inline any data from the raw JSON files.
- `risk_profile` (from Step 1)
- `accuracy_baseline` (from Step 3b) — computed before spawning the agent, passed as a single-line summary: `"Accuracy: N/M correct, beat SPY K/M. Top winner: SYM +X%. Top miss: SYM -Y%."`
- The MegaAgent prompt from `references/agent-prompts.md`

**Instructions to include with DATA_CONTEXT:**
> "News headlines and keyword sentiment have been pre-fetched in DATA_CONTEXT. Use them as the primary source for `key_news` and `sentiment`. Only do additional web searches for missing catalyst context or to verify the top 2–3 highest-conviction picks. Use SEC risk bullets in DATA_CONTEXT as primary `key_risks`. CORRELATION_LIMITS in DATA_CONTEXT are hard rules — never exceed `max=N` picks per group."

**Prompt size guardrail (enforced by compress_context.py):**
- Target: ≤ 7,500 characters for DATA_CONTEXT. The script warns to stderr if exceeded.
- Never paste raw JSON arrays inline — always use the compressed output.
- Never paste the Block 2 output schema inline — it is already in `references/agent-prompts.md`.

Use the **MegaAgent prompt** from `references/agent-prompts.md` (section: `## MegaAgent (Combined Research + Strategy)`) as the subagent system prompt. The MegaAgent returns **only Block 2** (strategy JSON). Block 1 (sectors) was already built by Step 4a. The Block 2 schema is defined in that file.

### Step 5: Build + Write Report Data

Assemble REPORT_DATA from Step 4a (sectors) and Step 4b (MegaAgent Block 2):

```python
import json

sectors   = json.load(open("/tmp/sectors.json"))      # built by Step 4a
strategy  = <MegaAgent Block 2 JSON>                  # from Step 4b

# Optionally enrich sectors with MegaAgent picks:
# python3 tools/build_sectors.py --out /tmp/sectors.json --enrich-picks /tmp/picks.json

report_data = {
  "brand": "Tododeia", "creator": "@quebert",
  "generated_at": "ISO 8601", "risk_profile": strategy["risk_profile"],
  "executive_summary": strategy["strategy_summary"],
  "macro_environment": strategy["macro_environment"],
  "portfolio_allocation": strategy["portfolio_allocation"],
  "cross_sector_insights": strategy["cross_sector_insights"],
  "risk_adjusted_picks": strategy["risk_adjusted_picks"],
  "historical_accuracy": strategy["historical_accuracy"],
  "warnings": strategy.get("warnings", []),
  "sectors": sectors,
  "spy_price_at_report": "<today_market_context.macro.spy_price>"
}
```

`spy_price_at_report` records the S&P 500 level at the time of this report. The **next** run reads this from the history file to compute alpha (pick return minus SPY return) for each position.

Then write REPORT_DATA to a temp file and call:
```
python3 tools/write_report.py /tmp/report_data.json
```

`write_report.py` validates the schema, then writes both `output/history/YYYY-MM-DD.json` and `dashboard/public/data/report.json` using temp-then-rename — either both files are updated or neither is. It also prunes history to the last 30 files. If validation fails, it exits with a non-zero code and prints the missing fields — re-prompt the MegaAgent to fill them in.

**Fallback (legacy HTML):** If `dashboard/package.json` does not exist, additionally read `assets/template.html`, replace `{{REPORT_DATA_JSON}}` with the serialized JSON, and write to `output/report.html`.

### Step 7: Serve the Report

**Primary (Next.js dashboard):**
1. Check if `dashboard/node_modules/` exists. If not, run `npm install --prefix dashboard`.
2. Check if port 3420 is in use: `lsof -i :3420`. If already running, skip — user just refreshes.
3. If not running: `npm run dev --prefix dashboard -- -p 3420` (background).
4. Tell the user:

> **Tododeia Investment Report is ready!**
> Open: http://localhost:3420
>
> **Profile**: {risk_profile} | **Top Pick**: {#1 risk-adjusted pick} | **Portfolio**: {allocation summary}
>
> The report includes cross-sector strategy analysis, social sentiment, historical accuracy tracking, and interactive charts.

**Fallback (legacy):** `python3 -m http.server PORT --directory output` on port 8420-8425.

## Error Handling

- If `WebSearch` returns no results for an asset, try `WebFetch` on known financial sites (Yahoo Finance, CoinGecko, Google Finance).
- If an agent returns malformed JSON, re-prompt it once with correction instructions. If it still fails, mark that sector as `"data_unavailable": true`.
- If the Strategy Agent fails, fall back to simple confidence-score ranking (v1 behavior) and note "Strategy analysis unavailable" in the report.
- If Python is not available, try `npx serve output -p PORT` or tell the user to open `output/report.html` directly in their browser.
- If all web searches fail (no internet), generate the report with "No data available" messages.
- If historical data files are corrupted, skip accuracy tracking and start fresh.

## Important Notes

- Always use today's date when constructing search queries.
- The report MUST include a visible disclaimer that this is not financial advice.
- Never cache or reuse old data — every invocation does fresh research.
- Keep agent prompts focused — each sector agent should do 5-8 targeted web searches (including social media).
- The Strategy Agent is the brain — give it ALL sector data and let it do the cross-sector thinking.
- Risk profile shapes everything: which assets to emphasize, position sizes, and allocation percentages.
