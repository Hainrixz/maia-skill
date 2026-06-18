# Contributing to Tododeia

Thanks for helping improve this skill. It's a personal/community tool — keep changes
focused and run the checks below before opening a PR.

## Project layout

- `SKILL.md` — the orchestrator the skill runs (5-agent workflow).
- `references/agent-prompts.md` — the 5 sub-agent prompts (hybrid data sourcing).
- `assets/template.html` — standalone HTML report (fallback when Node isn't available).
- `dashboard/` — the Next.js dashboard (primary report UI).
- `.claude-plugin/plugin.json` — plugin manifest.

## The data contract

`REPORT_DATA` is the single shared schema across the skill, the JSON files, and the UI.
It lives in three places that must stay aligned:

1. `dashboard/src/types/report.ts` — the TypeScript types.
2. `dashboard/schema/report.schema.json` — the executable JSON Schema (CI validates the
   sample reports against it).
3. `SKILL.md` Step 4/5 — the schema the agents are told to emit.

Rules: monetary/numeric fields are **numbers or `null`** (never strings with `$`, `%`, or
separators); `change_*` are signed percent numbers; formatting happens only at render time
via `dashboard/src/lib/utils.ts`. If you change a field, update all three places and the
sample reports in `dashboard/public/data/`.

## Before pushing

```bash
npm ci --prefix dashboard
npm run lint --prefix dashboard
npm run build --prefix dashboard
# validate sample reports against the contract
npx ajv-cli@5 validate -s dashboard/schema/report.schema.json -d dashboard/public/data/report.json
```

Run the dashboard locally with `npm run dev --prefix dashboard` (http://localhost:3000)
or test the skill end-to-end from Claude Code ("run an investment analysis").

## Versioning

Bump the version in **both** `SKILL.md` (frontmatter) and `.claude-plugin/plugin.json`
together (CI fails if they differ), and add a `CHANGELOG.md` entry.
`dashboard/package.json` version is internal to the app and tracked separately.

## i18n

All user-visible strings go through `dashboard/src/lib/translations.ts` (`t("key")`).
Add new keys to **both** `en` and `es`. Don't render raw enum values (e.g. `bullish`,
`buy`) — map them through a translation key.
