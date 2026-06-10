# Versioning — Pocket Confidant

Single source of truth: **`VERSION`** at the repo root.

The system is **git-aware** and **idempotent**. Run it as often as you like; it
only writes when something has actually changed. Build numbers are derived
from `git rev-list vX.Y.Z..HEAD --count` — no counter file, no drift, naturally
resets on the next release tag.

## The four states

| `VERSION`             | When                                              | State                  |
|-----------------------|---------------------------------------------------|------------------------|
| `0.2.0-dev`           | Working on 0.2.0, **no tag yet**                  | pre-release            |
| `0.2.0`               | Tag `v0.2.0` exists, **0 commits since**          | released (clean)       |
| `0.2.0-build001`      | Tag `v0.2.0` exists, **1 commit since**           | released (post-build)  |
| `0.2.0-build042`      | Tag `v0.2.0` exists, **42 commits since**        | released (post-build)  |

The state is **auto-detected** by inspecting git. You never compute a build
number by hand; you never maintain a counter file.

## Quick start

```bash
# Compute the right VERSION (idempotent, no-op if already correct)
python scripts/bump_version.py

# Just show the value, don't write
python scripts/bump_version.py --print

# See what the metadata.json would contain
python scripts/bump_version.py --json
```

## Releasing a version (the only manual step)

When you're ready to release `0.2.0`:

```bash
# 1. Make sure VERSION is the right base (default: edit directly)
echo "0.2.0-dev" > VERSION       # or use: python scripts/bump_version.py --set 0.2.0-dev

# 2. Commit everything that should be in the release
git add -A
git commit -m "chore: cut v0.2.0"

# 3. Tag it (this is what the system looks for to mark "released")
git tag v0.2.0
git push origin v0.2.0

# 4. Re-run the script — it detects the tag and rewrites VERSION to clean
python scripts/bump_version.py
# 🟢 0.2.0  (released-clean, ...)

# 5. OPTIONAL: turn on the pre-commit hook so future commits auto-bump
bash scripts/install-hooks.sh
```

From this point on, every commit increments the build number automatically:

```bash
git commit -m "fix: typo"
# pre-commit hook runs bump_version.py
# VERSION: 0.2.0 → 0.2.0-build001
```

## Bumping to the next release (0.2.0 → 0.3.0)

```bash
# Start the next release line
python scripts/bump_version.py --set 0.3.0-dev

# (work on 0.3.0...)

# When ready
git tag v0.3.0
python scripts/bump_version.py
# 🟢 0.3.0  (released-clean, ...)

# Now commits auto-bump to 0.3.0-buildNNN
```

The system never confuses `0.2.0` builds with `0.3.0` builds — each release
has its own tag, its own count, its own build sequence.

## Why it's truly automatic

- **Build number = commit count since the matching tag.** Computed at runtime
  from `git rev-list vX.Y.Z..HEAD --count`. There's nothing to forget to update
  and no counter file to lose.
- **"Released" detection = presence of tag `vX.Y.Z`.** You don't have to tell
  the system "we released" — the tag IS the signal. Push the tag and the next
  bump run flips state automatically.
- **Idempotent.** The script writes only when the computed value differs from
  what's in `VERSION`. Safe to wire into pre-commit, CI, cron, or just run
  by hand — it will never dirty the tree unnecessarily.

## What writes what

| File             | Written by                       | Read by                |
|------------------|----------------------------------|------------------------|
| `VERSION`        | `bump_version.py` (or you, manually) | the script, the UI  |
| `metadata.json`  | `bump_version.py`                | the UI footer, CI      |
| `git tag vX.Y.Z` | you                              | the script             |

Both `VERSION` and `metadata.json` are committed to the repo (they're small
and act as a snapshot of the state at last commit). The UI also reads
`metadata.json` at startup so it always shows fresh data even between commits.

## Files

```
VERSION                       # source of truth (one line)
metadata.json                 # generated snapshot for UI/CI consumption
scripts/bump_version.py       # the script
scripts/install-hooks.sh      # opt-in: install the pre-commit hook
.githooks/pre-commit          # the hook (not installed by default)
```

## Uninstalling the hook

```bash
bash scripts/install-hooks.sh --uninstall
```

The script and metadata keep working — the hook is purely a convenience.
