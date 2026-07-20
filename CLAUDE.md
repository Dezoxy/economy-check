# CLAUDE.md

@AGENTS.md

## Claude Code specifics

- Hooks are live in this repo (`.claude/settings.json`): network egress is
  allowlisted from `data/sources.yaml`; writes to `*/reports/*.md` are linted;
  a Stop gate blocks finishing when a written report lacks a passing
  `<report>.score.json`. If a hook blocks you, fix the report — never the hook.
- Report skills: invoke as `/weekly-market-update [YYYY-MM-DD]` (more report types
  arrive with Phase 1 steps E–G).
- Subagents live in `.claude/agents/` — analysts return sourced briefs; the
  fact-checker and editor are the verification pair. Keep generator ≠ verifier:
  never have the composing session score its own rubric.
- Headless runs use `shared/scripts/run_job.sh` (launchd/cron); interactive runs
  should end with the delivery question, not an automatic send.
- Python here is stdlib-only by design (bare python3 on Mac + Cowork). The single
  exception is matplotlib for charts. Don't add dependencies casually.
