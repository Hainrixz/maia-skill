# Tododeia — Investment Analysis Skill for Claude Code

**by @quebert** · [modCarlos/maia-skill](https://github.com/modCarlos/maia-skill)

A Claude Code skill that pre-fetches real market data for 60+ tickers using Python tools, then spawns a single MegaAgent to produce a risk-adjusted portfolio with investment theses, carry-forward of active positions, and a Next.js dashboard.

> **[Leer en Español](#español)**

---

## How It Works

```
  "run tododeia" / "analyze markets"
           │
           ▼
  ┌─────────────────────┐
  │  Risk profile prompt │  conservative / moderate / aggressive
  └────────┬────────────┘
           │
           ▼  Python tools (no LLM needed)
  ┌─────────────────────────────────────────────────────┐
  │  pre_fetch.py       — yfinance data for 60 tickers  │
  │  news_fetch.py  ┐                                   │
  │  sec_risk_fetch ┘ parallel — headlines + 10-K risks │
  │  accuracy_windows.py — 1d/5d/30d pick accuracy      │
  │  update_stops.py     — ATR trailing stops           │
  │  compress_context.py — compact ~7,500 char context  │
  └────────────────────────┬────────────────────────────┘
                           │  /tmp/mega_context.txt
                           ▼
              ┌────────────────────────┐
              │       MegaAgent        │
              │   (Claude Sonnet 4.x)  │
              │                        │
              │  • Applies CORRELATION │
              │    LIMITS (hard rules) │
              │  • Carry-forward of    │
              │    active positions    │
              │  • 13 risk-adj. picks  │
              │    with thesis +       │
              │    invalidators        │
              └────────────┬───────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
   output/history/   active_positions  dashboard/
   YYYY-MM-DD.json       .json         public/data/
                                           │
                                           ▼
                                  Next.js localhost:3420
```

## What Changed from the Original

This fork diverged significantly from the upstream project:

| Feature | Original | This fork |
|---------|----------|-----------|
| Architecture | 5 parallel AI agents (4 sector + 1 strategy) | Pre-fetch tools + 1 MegaAgent |
| Asset universe | Dynamic discovery by agents | Fixed 60-ticker screened list |
| Data source | Agent web searches | yfinance (real market data, no LLM searches) |
| Sectors | Crypto, Stocks, Forex, Commodities | Stocks + commodities/gold integrated |
| Active positions | None | Carry-forward between sessions |
| Split detection | None | Hard exclusion when split detected (±60 days) |
| Accuracy tracking | Basic | 1d / 5d / 30d windows with outlier filtering |
| Trailing stops | None | ATR-based, updated every run |
| Context to LLM | Raw per-sector JSON | Compressed 7,500-char structured block |

## Features

- **Pre-fetched real data**: RSI, trend, support/resistance, ATR, Altman Z, Piotroski score, insider signals — all from yfinance, zero LLM web searches for technicals
- **Risk profiles**: Conservative, moderate, aggressive — position sizes and allocation change accordingly
- **Carry-forward**: Active positions persist between sessions; excluded only when thesis explicitly invalidated
- **Split detection**: Tickers with recent stock splits are automatically excluded from the screener
- **Multi-window accuracy**: 1-day, 5-day, 30-day accuracy tracked per session — fed back to the MegaAgent
- **Trailing stops**: ATR-14 based stops that only move up, updated every run
- **Interactive dashboard**: Next.js on `localhost:3420` with bilingual support (EN/ES)
- **History**: Every session saved to `output/history/YYYY-MM-DD.json` for backtesting and accuracy tracking

## Requirements

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Python 3.9+ with `yfinance` (`pip install yfinance`)
- Node.js 18+ (for the dashboard)
- Internet connection (yfinance + news fetch need it)

## Installation

### Option A: One-liner

```bash
curl -sL https://raw.githubusercontent.com/modCarlos/maia-skill/main/install.sh | bash
```

Clones the repo, symlinks the skill into Claude Code, and installs dashboard dependencies.

### Option B: Manual

```bash
# 1. Clone
git clone https://github.com/modCarlos/maia-skill.git

# 2. Symlink into Claude Code
mkdir -p ~/.claude/plugins
ln -s "$(pwd)/maia-skill" ~/.claude/plugins/maia-skill

# 3. Install Python dependencies
pip install yfinance pandas numpy requests

# 4. Install dashboard dependencies
npm install --prefix maia-skill/dashboard
```

## Usage

In any Claude Code conversation:

```
"run tododeia"
"run tododeia moderate"
"analyze markets aggressive"
"investment analysis conservative"
```

You'll be asked your risk profile if not provided, then the pipeline runs. The report opens at `http://localhost:3420`.

To start the dashboard manually:
```bash
cd ~/.claude/plugins/maia-skill/dashboard && npm run dev -- -p 3420
```

## Project Structure

```
maia-skill/
  SKILL.md                    # Orchestrator instructions (read by Claude)
  tools/
    pre_fetch.py              # yfinance screener for 60 tickers
    news_fetch.py             # Headlines + sentiment pre-fetch
    sec_risk_fetch.py         # SEC 10-K risk factor pre-fetch
    accuracy_windows.py       # 1d/5d/30d accuracy computation
    update_stops.py           # ATR trailing stop updater
    build_sectors.py          # Deterministic sectors JSON (no LLM)
    compress_context.py       # Compact context builder for MegaAgent
    write_report.py           # JSON validator + atomic file writer
  references/
    agent-prompts.md          # MegaAgent system prompt + Block 2 schema
    model-comparison.md       # LLM model selection guide for this project
  data/                       # Runtime data (gitignored)
    market_context.json       # pre_fetch output
    news_context.json         # news_fetch output
    sec_risk_context.json     # sec_risk_fetch output
    trailing_stops.json       # update_stops output
    active_positions.json     # carry-forward state
  output/
    history/                  # YYYY-MM-DD.json per session
  dashboard/                  # Next.js interactive dashboard
    src/
      app/                    # App router
      components/report/      # UI components
      hooks/                  # Language + data hooks
      lib/                    # Translations, constants
      types/                  # TypeScript types
    public/data/              # Generated report JSON (runtime)
  assets/
    template.html             # Static HTML fallback
```

## Customization

### Ticker Universe

Edit `tools/pre_fetch.py` — the `TICKERS` list near the top defines the full screened universe. Add or remove tickers freely. Split detection and ATR calculations apply to all tickers automatically.

### MegaAgent Prompt & Pick Schema

Edit `references/agent-prompts.md`. The `## MegaAgent` section controls how the LLM reasons about picks. The Block 2 JSON schema (required fields per pick) is defined there too.

### Correlation Limits

In `tools/compress_context.py`, the `CORRELATION_GROUPS` dict defines which tickers count toward which group cap. Add groups or adjust the `max` per group to control sector concentration.

### Dashboard

Tailwind CSS. Edit components in `dashboard/src/components/report/`. UI translations are in `dashboard/src/lib/translations.ts`.

## Model Recommendation

See `references/model-comparison.md` for a full analysis. **TL;DR:**

| Use case | Recommended model |
|----------|------------------|
| Daily runs | Claude Sonnet 4.x |
| Weekly deep-dive | Claude Opus 4 |
| Budget alternative | Gemini 2.5 Pro |
| Do NOT use | Claude Haiku 3.5, GPT-4o mini |

## Disclaimer

This tool is for **informational and educational purposes only**. It does not constitute financial advice. AI-generated analysis may contain errors. Always consult a qualified financial advisor. Past performance is not indicative of future results.

---

<a id="español"></a>

# Tododeia — Skill de Análisis de Inversiones

**por @quebert** · [modCarlos/maia-skill](https://github.com/modCarlos/maia-skill)

Skill de Claude Code que pre-fetcha datos reales de mercado para 60+ tickers con herramientas Python, luego lanza un MegaAgent para generar un portafolio ajustado por riesgo con tesis de inversión, carry-forward de posiciones activas y un dashboard en Next.js.

> **[Read in English](#tododeia--investment-analysis-skill-for-claude-code)**

## Cómo funciona

El pipeline tiene dos fases:

**Fase 1 — Python tools (sin LLM, ~30–60s):**
- `pre_fetch.py` — RSI, tendencia, soportes, ATR, Altman Z, Piotroski para 60 tickers vía yfinance
- `news_fetch.py` + `sec_risk_fetch.py` — headlines y riesgos 10-K en paralelo
- `accuracy_windows.py` — precisión histórica en ventanas de 1d/5d/30d
- `update_stops.py` — trailing stops ATR que solo suben
- `compress_context.py` — comprime todo a ~7,500 chars para el MegaAgent

**Fase 2 — MegaAgent (Claude Sonnet 4.x, ~40s):**
- Recibe el contexto comprimido
- Aplica CORRELATION_LIMITS (reglas duras por sector)
- Mantiene posiciones activas (carry-forward) entre sesiones
- Genera 13 picks con thesis específico + invalidadores + stops

**Salida:**
- `output/history/YYYY-MM-DD.json` — historial de sesiones
- `data/active_positions.json` — estado de posiciones activas
- Dashboard en `localhost:3420`

## Requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Python 3.9+ con `yfinance` (`pip install yfinance`)
- Node.js 18+ (para el dashboard)
- Conexión a internet

## Instalación

```bash
# Opción A: Una línea
curl -sL https://raw.githubusercontent.com/modCarlos/maia-skill/main/install.sh | bash

# Opción B: Manual
git clone https://github.com/modCarlos/maia-skill.git
mkdir -p ~/.claude/plugins
ln -s "$(pwd)/maia-skill" ~/.claude/plugins/maia-skill
pip install yfinance pandas numpy requests
npm install --prefix maia-skill/dashboard
```

## Uso

```
"corre tododeia"
"corre tododeia moderado"
"análisis de inversiones agresivo"
```

El reporte se abre en `http://localhost:3420`.

Para iniciar el dashboard manualmente:
```bash
cd ~/.claude/plugins/maia-skill/dashboard && npm run dev -- -p 3420
```

## Aviso Legal

Esta herramienta es **solo para fines informativos y educativos**. No constituye asesoramiento financiero. El análisis generado por IA puede contener errores. Siempre consulta a un asesor financiero calificado. El rendimiento pasado no es indicativo de resultados futuros.

## Licencia

MIT — ver [LICENSE](LICENSE)
