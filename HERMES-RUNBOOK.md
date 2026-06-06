# Petriarium Hermes Runbook

Use this when Hermes is coordinating the Petriarium build with tmux and two
OpenCode worker lanes.

## Goal

Keep the workers isolated, keep the board visible, and make the skeptic role
explicit before the run starts.

## tmux layout

- `petriarium-control` - Hermes board / coordinator
- `petriarium-deepseek` - OpenCode worker using `opencode/deepseek-v4-flash-free`
- `petriarium-minimax` - OpenCode worker using `opencodego-minimax-m3`
- `petriarium-skeptic` - one randomly selected lane from the two workers above

## Start the board

```bash
tmux new-session -d -s petriarium-control -c /mnt/homes/galileo/argo/Development/build-small-2026 'hermes'
tmux split-window -h -t petriarium-control -c /mnt/homes/galileo/argo/Development/build-small-2026
tmux send-keys -t petriarium-control:0.0 'opencode run -m opencode/deepseek-v4-flash-free --dir /mnt/homes/galileo/argo/Development/build-small-2026 -- "Read HERMES-RUNBOOK.md, implement the current Petriarium ticket, and write output only into your own run folder."' Enter
tmux send-keys -t petriarium-control:0.1 'opencode run -m opencodego-minimax-m3 --dir /mnt/homes/galileo/argo/Development/build-small-2026 -- "Read HERMES-RUNBOOK.md, implement the current Petriarium ticket, and write output only into your own run folder."' Enter
```

If Hermes uses separate windows instead of panes, keep the same commands and
just change the tmux target. The important part is the model split and the
isolation rule.

## Skeptic rule

Before dispatch:

1. Randomly pick one of the two lanes to be the skeptic.
2. Announce it in the board note.
3. Tell both lanes that the skeptic lane is responsible for pressure-testing
   assumptions, not for blocking progress.

## Worker boundaries

- Do not let both workers edit the same files at once.
- Let each worker write to its own run folder first.
- Only the integration pass should merge code into the repo.
- Keep a log file for each worker and a board note for Hermes.

## Suggested Petriarium tasks

1. DeepSeek lane: implement or refine the app UI, artifact shelf, and state panel.
2. MiniMax lane: review the user flow, demo clarity, and failure handling.
3. Skeptic lane: pressure-test the product loop, verify the user can understand
   the app cold, and call out any missing proof.
4. Hermes: merge the best pieces, keep the board current, and stop drift.

## Verification

- Run `python tests/run_petriarium.py`
- Launch `python apps/petriarium/app.py`
- Confirm the page loads at `http://127.0.0.1:7861`
- Check that the creature, receipts, artifacts, and events all render

