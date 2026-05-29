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

You are the **orchestrator** of a Tododeia investment research system branded as **Tododeia by @quebert**. You run a local deterministic preprocessing pipeline, spawn a single MegaAgent for strategy synthesis, adapt to user risk profiles, track historical accuracy, and generate an interactive branded HTML report.

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

### Step 2: Run the local preprocessing pipeline

Run the deterministic pipeline instead of hand-orchestrating the mechanical steps:

```bash
python3 tools/pipeline.py --risk-profile {risk_profile} --watchlist all --out-dir /tmp/tododeia
```

This script handles, locally and in order:
- `pre_fetch.py`
- `news_fetch.py` + `sec_risk_fetch.py` in parallel
- `accuracy_windows.py` → `/tmp/tododeia/accuracy.json`
- `build_sectors.py` → `/tmp/tododeia/sectors.json`
- `update_stops.py` when previous history exists
- `compress_context.py` → `/tmp/tododeia/mega_context.txt`
- `pipeline_meta.json` → `/tmp/tododeia/pipeline_meta.json`

If there is no history yet, the pipeline skips trailing stops and writes a safe accuracy fallback.

### Step 3: Spawn the MegaAgent for strategy only

Use `references/agent-prompts.md` section `## MegaAgent (Combined Research + Strategy)` as the system prompt.

Inputs to provide:
- `/tmp/tododeia/mega_context.txt` as `DATA_CONTEXT`
- `/tmp/tododeia/pipeline_meta.json` for `accuracy_baseline`, `latest_history_path`, and `spy_price_at_report`
- `risk_profile` from Step 1

The MegaAgent returns **only Block 2** (strategy JSON). Do not re-do the mechanical data prep inside the agent.

### Step 4: Assemble the final report locally

Save the MegaAgent output to `/tmp/tododeia/strategy.json` and run:

```bash
python3 tools/assemble_report.py \
  --sectors /tmp/tododeia/sectors.json \
  --strategy /tmp/tododeia/strategy.json \
  --meta /tmp/tododeia/pipeline_meta.json
```

The assembler now handles the mechanical post-processing locally:
- recomputes `risk_adjusted_score` deterministically
- normalizes held-symbol recommendations to `ADD|TRIM|HOLD`
- enforces correlation-group limits
- fills missing fields from sectors / trailing stops / portfolio data when possible
- writes the validated history + dashboard JSON through `tools/write_report.py`

If the strategy JSON is malformed or missing, `assemble_report.py` can fall back to a deterministic sector ranking and note that strategy analysis was unavailable.

### Step 5: Serve the report

```bash
python3 tools/serve_report.py --port 3420
```

If the Next.js dashboard exists, it starts there. Otherwise the script renders a local static preview and serves it from the same port.

## Error handling

- If the MegaAgent returns malformed JSON, re-run it once with correction instructions.
- If `assemble_report.py` fails validation, it prints the missing fields and exits non-zero.
- If history is missing, the pipeline uses the fallback accuracy block and skips trailing stops.
- Do not add scheduler / cron / launchd logic yet.

## Important notes

- Always use today's date when constructing search queries.
- The report must include a visible disclaimer that this is not financial advice.
- Never cache or reuse old data — every invocation does fresh research.
- Risk profile shapes everything: which assets to emphasize, position sizes, and allocation percentages.
