---
name: investment-analysis
version: 2.0.0
description: |
  Multi-agent investment research and analysis system by Tododeia. Use when the user wants
  market analysis, investment research, or a summary of current opportunities across crypto,
  stocks, forex, and commodities. Spawns 5 specialized research agents (4 sector + 1 strategy),
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

### Step 3: Load Agent Prompts + Historical Data (parallel)

In the same turn, do both in parallel:

**3a. Agent prompts**: Read `references/agent-prompts.md` relative to this skill's directory. Use the Glob tool to find this skill's installation path by searching for `**/investment-analysis/references/agent-prompts.md`.

**3b. Historical data**: Read the most recent JSON file from `output/history/` (format `YYYY-MM-DD.json`). Extract:
- `risk_adjusted_picks` — the previous picks with `entry_price` values
- `risk_adjusted_picks[].thesis` — the investment reasoning recorded at pick time
- `risk_adjusted_picks[].thesis_invalidators` — conditions that would break the thesis
- `risk_adjusted_picks[].thesis_status` — `active | updated | invalidated`

Then read `data/market_context.json` from the PREVIOUS run to load `prices_snapshot` — this is the ground-truth price baseline for accuracy tracking. The `prices_snapshot[symbol].price` is the **immutable price recorded at fetch time** and must be used instead of reconstructed or web-searched prices.

**Accuracy formula (use this exactly)**:
```
# SPY baseline for alpha — spy_price_at_report stored in the previous history file
spy_then = previous_history_file.get("spy_price_at_report")  # None for old runs
spy_now  = today_market_context["macro"]["spy_price"]         # always present

for each previous pick:
    current_price = prices_snapshot[symbol].price  # from TODAY's market_context.json
    entry_price   = pick.entry_price               # from PREVIOUS history file
    pick_return   = (current_price - entry_price) / entry_price
    correct       = pick_return > 0                # absolute: price went up
    # Alpha — only computed when spy_then is available (graceful degradation):
    if spy_then:
        spy_return  = (spy_now - spy_then) / spy_then
        alpha       = pick_return - spy_return      # positive = outperformed SPY
        beat_market = alpha > 0
```
Pass `alpha` per pick in `accuracy_baseline` so the MegaAgent can report "beat SPY: X/N" inside `historical_accuracy`.

Build a `previous_theses` dict to pass to the MegaAgent:
```
previous_theses = {
  symbol: {
    "thesis": pick.thesis,
    "invalidators": pick.thesis_invalidators,
    "entry_price": pick.entry_price,
    "status": pick.thesis_status,
    "price_then": pick.entry_price,
    "price_now": prices_snapshot[symbol].price  # from today's pre-fetch
  }
  for pick in previous_picks if pick.thesis is not None
}
```

If `prices_snapshot` is missing from the previous context file (older runs), fall back to the MegaAgent web search as before. If no history or no `thesis` field exists (old run format), pass `previous_theses = {}` and skip thesis evaluation silently.

### Step 4: Spawn Research + Strategy MegaAgent

**Fix 5 — single subagent** replacing the previous 4 sector agents + strategy agent. Launch **one MegaAgent** using the Agent tool. This reduces orchestrator context pressure and eliminates the intermediate turn between sector agents and the strategy agent.

Pass the MegaAgent:
- `SCREENED_CANDIDATES` **compact table**: top 12-15 by entry quality + RSI (from `data/market_context.json` → `candidates[]`) with only: symbol, **price_at_fetch**, RSI, entry_quality, trend, fwd_PE, PEG, earnings_days_away, **correlation_group**
- `NEWS_CONTEXT` (from `data/news_context.json` → `news{}`) — injected as a compact block per ticker. Tell the MegaAgent: **"News headlines and keyword sentiment have been pre-fetched below. Use `key_news[0..1]` as the 2 required headlines per pick and `sentiment.label` as the default sentiment value. Only do additional web searches for missing catalyst context or to verify the top 2-3 highest-conviction picks — do NOT search for headlines already present."** Format each ticker as: `SYMBOL: [sentiment_label | analyst_rec] → headline_1 | headline_2`. This alone eliminates ~20 web searches per run.
- `CORRELATION_WARNINGS` (from `data/market_context.json` → `correlation_warnings[]`): list of over-concentration alerts. **Hard rule**: include at most `max_allowed` picks per group from `suggested_keep`. If a warning exists, do NOT include more than `max_allowed` picks from that group in `risk_adjusted_picks`.
- `MACRO_CONTEXT` (from `data/market_context.json` → `macro`) — VIX, F&G, regime, synthetic score
- `risk_profile` (from Step 1)
- `historical_picks` (from Step 3b, if available) — previous picks with `entry_price` values
- `accuracy_baseline` (from Step 3b) — dict of `{symbol: current_price}` built from today's `prices_snapshot`, cross-referenced against previous picks' `entry_price`. Compute accuracy **before** spawning the MegaAgent and pass the result directly. Do NOT ask the MegaAgent to reconstruct prices from web searches for accuracy purposes.
- `previous_theses` (from Step 3b) — dict of `{symbol: {thesis, invalidators, entry_price, price_then, price_now, status}}`. The MegaAgent MUST evaluate each thesis before ranking new picks (see Phase 0 below).
- The strategy agent prompt from `references/agent-prompts.md`

**Prompt size guardrail (required):**
- Keep the subagent prompt under ~8,000 characters.
- Never paste full 35+ candidate lists inline.
- Pass file paths (e.g. `data/market_context.json`) and instruct the subagent to read only required fields.

Use the **MegaAgent prompt** from `references/agent-prompts.md` (section: `## MegaAgent (Combined Research + Strategy)`) as the subagent system prompt. The MegaAgent returns two JSON blocks: Block 1 (sectors) and Block 2 (strategy). Both schemas are defined in that file.

### Step 5: Build + Write Report Data

Assemble REPORT_DATA from MegaAgent outputs:

```json
{
  "brand": "Tododeia", "creator": "@quebert",
  "generated_at": "ISO 8601", "risk_profile": "moderate",
  "executive_summary": "<MegaAgent strategy_summary>",
  "macro_environment": "<Block 2>", "portfolio_allocation": "<Block 2>",
  "cross_sector_insights": "<Block 2>", "risk_adjusted_picks": "<Block 2>",
  "historical_accuracy": "<Block 2>", "warnings": [],
  "sectors": "<Block 1 sectors>",
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
