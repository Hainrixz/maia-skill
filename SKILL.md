---
name: investment-analysis
version: 2.1.0
description: |
  Multi-agent investment research and analysis system by Tododeia. Use when the user wants
  market analysis, investment research, or a summary of current opportunities across crypto,
  stocks, forex, and commodities. Spawns 5 specialized research agents (4 sector + 1 strategy),
  adapts to user risk profile, tracks historical accuracy, and generates a branded interactive
  HTML report served locally. Educational analysis only — not financial advice.
  Trigger phrases: "investment analysis", "market research", "analyze markets",
  "investment opportunities", "what should I invest in", "market report",
  "tododeia", "investment advice", "portfolio recommendations", "run tododeia",
  "daily market analysis", "weekly report", "análisis de inversión",
  "analizar mercados", "reporte de mercado", "oportunidades de inversión".
user_invocable: true
---

# Tododeia Investment Analysis — Multi-Agent System v2

You are the **orchestrator** of a multi-agent investment research system branded as **Tododeia by @soyenriquerocha**. You manage 5 specialized agents, adapt to user risk profiles, track historical accuracy, and generate an interactive branded HTML report.

> **Educational framing (binding):** This skill produces **educational market analysis, not financial advice**. Never present output as a recommendation to buy or sell. Use analytical language ("signals favor accumulation", "consider", "watch", "reduce/avoid") rather than imperatives. The educational disclaimer MUST be shown to the user **before** the report (see Step 9).

## Workflow

Follow these steps exactly.

### Step 0: Resolve Paths and Capture the Analysis Date

Before anything else, establish a clean separation between the **read-only installed skill** and a **user-writable run location**, and capture the date once so every agent shares it.

1. **Find `SKILL_DIR`** (read-only — NEVER write into it): use the Glob tool to find `**/investment-analysis/references/agent-prompts.md`; `SKILL_DIR` is the directory two levels up from that match (the folder containing this `SKILL.md`). When invoked the skill is typically installed at `~/.claude/skills/investment-analysis` (a symlink) or `~/.claude/plugins/maia-skill`.
2. **Define the writable run location** (create as needed; this is where ALL generated artifacts go):
   - `RUN_DIR = ~/.claude/cache/tododeia`
   - `DASHBOARD_DIR = $RUN_DIR/dashboard` (a writable copy of the skill's dashboard)
   - `DATA_DIR = $DASHBOARD_DIR/public/data` (the dashboard serves these)
   - `HISTORY_DIR = $RUN_DIR/history`
   - `OUTPUT_HTML_DIR = $RUN_DIR/output` (legacy HTML fallback)
   - Rationale: the installed `SKILL_DIR/dashboard` may be a read-only symlink, and the user's current working directory is arbitrary. Writing relative paths against the CWD is the #1 cause of "no report generated". Always use these absolute `$RUN_DIR` paths.
3. **Capture the date once**: run `date -u +%Y-%m-%dT%H:%M:%SZ` and `date +%Y-%m-%d`. Store as `analysis_datetime` (ISO 8601 UTC) and `analysis_date` (YYYY-MM-DD). Pass these to every agent. Agents MUST use `analysis_date` for search queries and timestamps — they must NOT rely on their own clock or training-data notion of "today".
4. **Detect optional premium keys**: check the environment for `FINNHUB_API_KEY` and `POLYGON_API_KEY`. Record which (if any) are present and pass a `premium_stocks` flag (`finnhub` | `polygon` | `none`) to the stocks/materials agents. The skill works fully with free keyless endpoints when no key is set.

### Step 1: Determine Risk Profile

Ask the user their risk tolerance using the AskUserQuestion tool:

**Question**: "What's your investment risk profile?"
**Options**:
1. **Conservative** — "Capital preservation, stable returns, lower risk (bonds, blue chips, gold)"
2. **Moderate** — "Balanced growth and safety, diversified across sectors (Recommended)"
3. **Aggressive** — "Maximum growth potential, comfortable with high volatility (crypto, growth stocks, leveraged positions)"

Store the selected profile as `risk_profile` ("conservative", "moderate", or "aggressive"). If the response is not one of these three, re-prompt. This profile is passed to the Strategy Agent and shapes the analytical emphasis.

### Step 2: Load Agent Prompts

Read `$SKILL_DIR/references/agent-prompts.md`. This file contains the 5 agent prompts (4 sector + strategy).

### Step 3: Load Historical Data

Check `$HISTORY_DIR` for previous reports. If it exists, read the most recent JSON file (filenames use `YYYY-MM-DD.json`, which sorts chronologically). This historical data is passed to the Strategy Agent for accuracy tracking. If no history exists, this is the first run — that's fine.

### Step 4: Spawn 4 Sector Research Agents

Launch **all 4 agents in parallel** using the Agent tool in a single message. Pass each agent: its sector-specific prompt from `agent-prompts.md`, `analysis_date`/`analysis_datetime`, and the `premium_stocks` flag.

**Hybrid sourcing (binding):** each agent fetches **authoritative prices via WebFetch to keyless API endpoints first** (CoinGecko for crypto; Yahoo v8 chart / Frankfurter for the rest — see `agent-prompts.md`), and uses **WebSearch only for narrative, news, and social sentiment**. Each asset follows a fallback ladder: primary endpoint → alternate endpoint → WebSearch best-effort → `null` value with a note.

The 4 sector agents are:
1. **Crypto Agent** — 5-7 crypto assets (always BTC + ETH; dynamically finds trending/promising altcoins)
2. **Stocks Agent** — 5-8 stocks (always SPX + IXIC benchmarks; dynamically finds catalyst-driven names across sectors)
3. **Currencies Agent** — 5-7 currency pairs (always DXY + USD/MXN; dynamically finds event-driven pairs)
4. **Materials Agent** — 5-7 commodities (always Gold + Oil WTI; dynamically finds trending commodities)

Each agent MUST return a JSON block in this exact schema. **Data Contract: all monetary/numeric values are NUMBERS (or `null` if genuinely unavailable) — never strings with `$`, `%`, or thousands separators. Formatting happens only at render time.**

```json
{
  "sector": "crypto|stocks|currencies|materials",
  "timestamp": "{analysis_datetime}",
  "assets": [
    {
      "name": "Full Name",
      "symbol": "TICKER",
      "current_price": 67500.00,
      "price_unit": "USD|USD/oz|USD/bbl|rate|index",
      "change_24h": 2.3,
      "change_7d": -1.5,
      "change_30d": 12.8,
      "ytd_change": 45.2,
      "week_52_high": 73800.00,
      "week_52_low": 38500.00,
      "market_cap": 1300000000000,
      "volume_24h": 28000000000,
      "sentiment": "bullish|bearish|neutral|mixed|<short phrase>",
      "social_sentiment": "bullish|bearish|neutral|mixed|<short phrase>",
      "social_buzz": "high|medium|low",
      "confidence": 7,
      "source_agreement": "high|medium|low",
      "data_source": "api|api_alt|websearch|unavailable",
      "sources_checked": ["api.coingecko.com", "finance.yahoo.com"],
      "key_news": ["headline 1", "headline 2"],
      "social_highlights": ["post 1", "post 2"],
      "recommendation": "buy|hold|sell",
      "reasoning": "1-2 sentence analytical explanation"
    }
  ],
  "sector_summary": "2-3 sentence overview of the sector",
  "sector_outlook": "bullish|bearish|neutral",
  "top_pick": "TICKER",
  "top_pick_reasoning": "Why this is the most notable opportunity in this sector"
}
```

Notes:
- `current_price` is a bare number. For currencies use the exchange rate (e.g. `17.39`) with `price_unit: "rate"`; for indices use the index level with `price_unit: "index"` and `market_cap: null`.
- `change_*` and `ytd_change` are signed numbers in **percent** (e.g. `2.3` means +2.3%, `-1.5` means −1.5%). No `%` sign.
- `recommendation` keeps the `buy|hold|sell` enum for internal filtering/sorting; the UI relabels it to analytical language (Consider/Hold/Avoid) at render time.

### Step 5: Spawn Strategy Agent

After all 4 sector agents return, launch the **Strategy Agent**. Pass it: all 4 sector JSON outputs, the `risk_profile`, historical data (if any), the strategy prompt, and **an explicit list of any sectors marked `data_unavailable`**.

The Strategy Agent performs cross-sector analysis and MUST return this JSON (same numeric Data Contract):

```json
{
  "risk_profile": "conservative|moderate|aggressive",
  "macro_environment": {
    "summary": "2-3 sentence macro overview (rates, inflation, geopolitics)",
    "interest_rate_outlook": "rising|stable|falling",
    "inflation_outlook": "rising|stable|falling",
    "geopolitical_risk": "high|medium|low",
    "key_factors": ["factor 1", "factor 2", "factor 3"]
  },
  "portfolio_allocation": {
    "crypto": 10,
    "stocks": 45,
    "currencies": 15,
    "materials": 20,
    "cash": 10
  },
  "cross_sector_insights": [
    { "insight": "Gold and crypto are both rallying...", "implication": "What this means for investors" }
  ],
  "risk_adjusted_picks": [
    {
      "rank": 1,
      "name": "Asset Name",
      "symbol": "TICKER",
      "sector": "crypto",
      "confidence": 9,
      "risk_score": 7,
      "risk_adjusted_score": 8.2,
      "recommendation": "buy",
      "reasoning": "Risk-adjusted reasoning for this profile",
      "position_size": "5-10% (illustrative allocation, not advice)"
    }
  ],
  "historical_accuracy": {
    "previous_date": "2026-03-12",
    "calls_made": 5,
    "calls_correct": 3,
    "accuracy_pct": 60,
    "notable": "BTC accumulation signal at $65k now at $67.5k (+3.8%)"
  },
  "warnings": ["Any risk warnings or cautions"],
  "strategy_summary": "3-4 sentence strategy overview tailored to risk profile"
}
```

**Partial-failure rule:** for any sector marked `data_unavailable`, the Strategy Agent MUST: exclude its assets from `risk_adjusted_picks`, set that sector's `portfolio_allocation` to `0`, **reassign the freed percentage to `cash`** (do not silently redistribute into other sectors), and add a `warnings[]` entry naming the missing sector. The allocation must still total 100.

### Step 6: Build the Report Data

Combine all agent outputs into the final REPORT_DATA object. For any failed sector, still include the key as `{ "sector": "<name>", "timestamp": "{analysis_datetime}", "assets": [], "data_unavailable": true, ... }` so the dashboard can show an empty-state card.

```json
{
  "brand": "Tododeia",
  "creator": "@soyenriquerocha",
  "generated_at": "{analysis_datetime}",
  "risk_profile": "moderate",
  "executive_summary": "Strategy agent's strategy_summary",
  "macro_environment": { },
  "portfolio_allocation": { },
  "cross_sector_insights": [ ],
  "risk_adjusted_picks": [ ],
  "historical_accuracy": { },
  "warnings": [ ],
  "sectors": {
    "crypto": { }, "stocks": { }, "currencies": { }, "materials": { }
  }
}
```

### Step 7: Save Historical Data

1. Create `$HISTORY_DIR` if needed.
2. Save REPORT_DATA as `$HISTORY_DIR/{analysis_date}.json`.
3. Keep only the last 30 files: list `$HISTORY_DIR/*.json`, sort by name (chronological), and delete the oldest until 30 remain.

### Step 8: Generate the Report

**Primary (Next.js dashboard):**
1. Ensure a writable copy of the dashboard exists at `$DASHBOARD_DIR`: if missing or stale, sync it from `$SKILL_DIR/dashboard` excluding `node_modules` and `.next` — `rsync -a --delete --exclude node_modules --exclude .next "$SKILL_DIR/dashboard/" "$DASHBOARD_DIR/"` (fallback to `cp -R` if `rsync` is unavailable).
2. Create `$DATA_DIR` if needed.
3. Write REPORT_DATA to `$DATA_DIR/report.json`.

**Fallback (legacy HTML template):**
If Node.js/npm is unavailable:
1. Read `$SKILL_DIR/assets/template.html`.
2. **Serialize REPORT_DATA safely** for embedding: run `JSON.stringify(REPORT_DATA)`, then in that JSON string replace `<` with `\u003c`, `>` with `\u003e`, U+2028 with `\u2028`, and U+2029 with `\u2029`. These are JSON unicode escapes: the JSON stays valid and parses back to the original, while no literal `</script>` or HTML can break out of the `<script type="application/json">` data island the template uses. Do NOT use HTML entities (`&lt;`) — the island is raw text and entities would corrupt the JSON.
3. Replace the token `{{REPORT_DATA_JSON}}` with the escaped JSON.
4. Create `$OUTPUT_HTML_DIR` if needed and write the populated HTML to `$OUTPUT_HTML_DIR/report.html`.

### Step 8b: Translate Report to Spanish

After writing the English report (primary path only — skip if the fallback HTML was used, which is single-language), spawn a **Translation Agent**:

1. Read `$DATA_DIR/report.json`.
2. Translate only these human-readable fields to Spanish: `executive_summary`, `strategy_summary`, `macro_environment.summary`, `macro_environment.key_factors[]`, `cross_sector_insights[].insight`, `cross_sector_insights[].implication`, `warnings[]`, `historical_accuracy.notable`; per sector `sector_summary`, `top_pick_reasoning`; per asset `reasoning`, `key_news[]`, `social_highlights[]`.
3. Do NOT translate: numbers, tickers, prices, dates, percentages, asset names, symbols, URLs, `price_unit`, `data_source`, or enum values (e.g. `bullish`, `buy`, `high`).
4. Write to `$DATA_DIR/report-es.json`.

> Translation prompt: "You are a financial translator. Translate the listed human-readable text fields of this investment report JSON from English to Spanish, iterating all nested levels (`sectors[].assets[].key_news[]`, etc.). Preserve all numbers, tickers, prices, dates, percentages, names, symbols, URLs, and enum values exactly. Return valid JSON with the same structure."

### Step 9: Serve the Report

**Always show the educational disclaimer FIRST**, then the URL:

> ⚠️ **Educational analysis — not financial advice.** Tododeia's signals are AI-generated opinions from public data and may be wrong. Do your own research and consult a licensed advisor before investing. You assume all risk.

**Primary (Next.js dashboard):**
1. If `$DASHBOARD_DIR/node_modules/` is missing, run `npm install --prefix "$DASHBOARD_DIR"`.
2. Check port 3420: `lsof -i :3420`. If a server is already running there, skip starting a new one (the user just refreshes).
3. Otherwise start it in the background: `npx --prefix "$DASHBOARD_DIR" next dev -p 3420` (run from `$DASHBOARD_DIR`).
4. Wait ~3 seconds, then tell the user:

> **Tododeia Investment Report is ready!** → http://localhost:3420
>
> **Profile**: {risk_profile} | **Top signal**: {#1 risk-adjusted pick} | **Illustrative allocation**: {summary}

**Fallback (legacy):**
If Node.js/npm is not available, serve `$OUTPUT_HTML_DIR`:
1. Find a free port starting at 8420 (try 8420-8425): `lsof -i :PORT`.
2. Start: `command -v python3 >/dev/null && python3 -m http.server PORT --directory "$OUTPUT_HTML_DIR" || python -m http.server PORT --directory "$OUTPUT_HTML_DIR"`.
3. Tell the user to open http://localhost:PORT/report.html (after the disclaimer).

### Step 10: Offer Scheduling

After showing the URL, mention (do NOT auto-configure):

> **Want recurring reports?** `/loop 24h /investment-analysis` (daily) or `/loop 168h /investment-analysis` (weekly). If `/loop` is unavailable, use `/schedule`. Or just run it manually anytime.

## Error Handling

- If `WebFetch` to a price endpoint fails or returns non-JSON, try the alternate endpoint, then `WebSearch`, then set the price fields to `null` with `data_source: "unavailable"`.
- If an agent returns malformed JSON, re-prompt once with correction instructions. If it still fails, or returns zero assets with a usable price, mark that sector `{ "assets": [], "data_unavailable": true }` and follow the partial-failure rule in Step 5.
- If the Strategy Agent fails, fall back to simple confidence-score ranking and note "Strategy analysis unavailable" in the report.
- If all web access fails (no internet), generate the report with `null` prices and "No data available" notes rather than failing.
- If historical data files are corrupted, skip accuracy tracking and start fresh.

## Important Notes

- **Educational, not advice** — the disclaimer in Step 9 is mandatory and must precede the report; recommendation language stays analytical.
- **Numbers internally, format on render** — agents emit raw numbers; the dashboard/template format prices, percentages, and dates (locale-aware EN/ES).
- Always use `analysis_date` (captured in Step 0) for searches and timestamps — never the model's own notion of "today".
- Never write into `$SKILL_DIR`; all artifacts go under `$RUN_DIR`.
- Never cache or reuse old market data — every invocation does fresh research.
- The Strategy Agent is the brain — give it ALL sector data (and the `data_unavailable` list) and let it do cross-sector synthesis.
- Risk profile shapes emphasis, illustrative position sizes, and allocation percentages.
