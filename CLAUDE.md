# Project instructions

## Git

Never run git commands that change repository state: no `git add`, `commit`, `checkout`,
`branch`, `merge`, `rebase`, `reset`, `stash`, `tag`, `push` or `pull`. When a change needs
to be made in git, write out the exact commands for the user to run themselves. Read-only
commands such as `git status`, `git log` and `git diff` are fine.

## Hardware work

The user performs every restore, backup and playback recording on the PO-33 and reports
back. Prepare restores with tracked `scripts/prepare_*` scripts, check results with
`scripts/check_*`, and record them with `scripts/finalize_*`. Predictions are registered
before data is taken, failed predictions are kept, and exploratory readings are labelled
as such. The feedback loop between the computer and the device is handled only by the
cable-swap prompts in `po33 hw run`, never by software echo removal or mixer modes.

## References

- `docs/format-reference.md`: everything verified about the backup format.
- `docs/fx-reference.md`: the measured behaviour of each effect.
- `docs/hardware-sessions.md`: how a hardware session runs.
- `docs/edit-plans.md`: the plan operations and their verification status.
- `docs/web-app-proposal.md`: the plan for the web app.
- `docs/archive-format.md`: the project and kit archive files the web app exports and imports.
- `docs/web-playback.md`: what the web app's preview playback reproduces and approximates.
- `docs/kit-sharing-results.md`: drum keys referencing another kit's buffer, verified, so kits are stored once.
- `docs/presets.md`: the ten preset projects the app ships with and how they are built and loaded.
- `docs/release.md`: how the local-only web app is built, hosted and audited for release.
- `docs/prior-art.md`: related projects, how this one compares, and open format questions.
- `docs/sound-synthesis.md`: how every bundled sound is synthesized, recipe by recipe.
- `docs/follow-ups.md`: the open questions and optional work left after the first release.
