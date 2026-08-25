# CLAUDE.md

@AGENTS.md

## Claude Code specifics

- Hooks are live in this repo (`.claude/settings.json`): network egress is
  allowlisted from `data/sources.yaml` (`net_allowlist.py`, PreToolUse on
  WebFetch|Bash); writes to `*/reports/*.md` are linted (`report_lint.py`,
  PostToolUse — naked numbers, template sections, tag freshness); a Stop gate
  (`quality_gate.py`) blocks finishing when a written report lacks a passing
  `<report>.score.json` (total ≥ 80, no category below 60% of its weight,
  3-attempt cap). If a hook blocks you, fix the report — never the hook.
- Known hook gaps, deliberately left open and tracked in PLAN.md's backlog:
  `net_allowlist.py` does not gate WebSearch results, and `report_lint.py`
  checks neither Hungarian quote pairing nor compound hyphenation. Do not
  treat "lint passed" as "F2 is clean".
- Report skills: `/weekly-market-update [YYYY-MM-DD]` for a live run,
  `dry-run` for the acceptance check (no report written), and
  `backtest YYYY-MM-DD` for a parity run against the corpus (writes to
  `crypto-analyst/reports/backtests/`, no ledger write, no PDF, no delivery).
  The other three report types (`event-note`, `onchain-review`,
  `altcoin-screen`) have templates + manifests but no skill yet — they get
  wired after Phase 1 step G.
- Subagents live in `.claude/agents/` — 4 analysts (macro, crypto, onchain,
  sentiment) return sourced briefs; the fact-checker and editor are the
  verification pair. Keep generator ≠ verifier: never have the composing
  session score its own rubric.
- **Mirrors, not forks.** `.codex/` (TOML agents, `hooks.json` with absolute
  paths, hook copies) and `.agents/skills/` hold copies of the `.claude/`
  config for other runtimes. Edit `.claude/` first, then re-copy into every
  mirror in the same commit — otherwise the quality plane silently forks.
- Headless runs use `shared/scripts/run_job.sh` (launchd/cron; resolves the
  claude CLI explicitly, wall-clock capped by `CLAUDE_TIMEOUT`, alerts on
  every failure path). Interactive runs should end with the delivery question,
  not an automatic send.
- Python here is stdlib-only by design (bare python3 on Mac + Cowork). Two
  exceptions, both already paid for: matplotlib for charts, and headless
  Chrome as a *system* tool for `render_pdf.py`. Don't add dependencies
  casually.
- `.pdf`/`.html` under `*/reports/` are gitignored derived artifacts —
  regenerate with `python3 shared/delivery/render_pdf.py <report.md>` rather
  than committing them.
- `settings.json` denies reading `.env` and force-pushing. Secrets currently
  in place: `FRED_API_KEY`. Still blank: `TELEGRAM_*`, `SMTP_HOST/USER/PASS`,
  `EMAIL_FROM` — so live delivery is untested and `deliver.py --dry-run` is
  the only proven path.
