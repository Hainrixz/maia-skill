# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/). The skill version lives in
`SKILL.md` (frontmatter) and `.claude-plugin/plugin.json` and must match (CI enforces this).

## [2.1.0]

Audit-driven stabilization and hardening pass.

### Fixed
- **Portability**: the skill now resolves its own install directory and writes all
  generated artifacts to a writable cache (`~/.claude/cache/tododeia`) instead of
  relative paths against the user's working directory — so a report actually generates
  when the skill is installed (not only when run from the repo).
- **Data contract**: prices, market caps, volumes and percent changes are now numbers
  end-to-end (agents → JSON → TypeScript types → dashboard/HTML), formatted only at
  render time. Removes the sort/format crash and the unformatted-number display.
- **Stored XSS** in the legacy HTML report: report data is embedded as an inert JSON
  island and every web-sourced string is HTML-escaped before rendering.
- Stale `jere-noticias-inver` glob, malformed `next dev` port command, and the
  `python3`/`python` fallback in `SKILL.md`.
- Partial sector-failure handling (a failed sector reweights its allocation to cash with
  a warning; charts no longer divide by zero).
- `install.sh` no longer swallows npm errors; adds rollback, broken-symlink repair, and
  a `python3` check.

### Added
- **Hybrid market data**: authoritative prices from keyless public APIs (CoinGecko,
  Yahoo Finance v8, Frankfurter) with a deterministic fallback ladder, plus optional
  `FINNHUB_API_KEY` / `POLYGON_API_KEY` for premium stock data.
- **Educational compliance**: a non-dismissable acknowledgment gate and a prominent
  disclaimer shown *before* the report (dashboard + HTML + orchestrator), with analytical
  ("Consider / Hold / Avoid") rather than directive language.
- Content-Security-Policy and security headers on the dashboard.
- Accessibility: chart ARIA labels, keyboard-operable sector cards and sortable headers,
  focus-visible rings, modal focus-trap/Escape, `prefers-reduced-motion`, and
  icon+text (not color-only) status badges.
- Full i18n: outlook/macro/recommendation/profile labels, dynamic `<html lang>`, and a
  notice when a Spanish report is missing (instead of silently showing English).
- JSON Schema for the report contract (`dashboard/schema/report.schema.json`), GitHub
  Actions CI (build + lint + schema validation + version parity + installer syntax),
  and `CONTRIBUTING.md`.

### Notes
- Dark mode is intentionally deferred (the dashboard currently uses hardcoded light
  colors; a partial migration would render inconsistently).

## [2.0.0]

- Multi-agent v2: 4 sector agents + 1 strategy agent, risk-profile adaptation,
  historical-accuracy tracking, and an interactive Next.js dashboard with EN/ES support.

## [1.0.0]

- Initial release: single-pass research with a static HTML report.
