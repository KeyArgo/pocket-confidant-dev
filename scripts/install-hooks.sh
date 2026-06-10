#!/usr/bin/env bash
# Install Pocket Confidant's git hooks (pre-commit auto-bumps VERSION).
#
# Run this AFTER you have tagged your first release (e.g. v0.2.0).
# Before that, run `python scripts/bump_version.py` manually when you want.
#
#   bash scripts/install-hooks.sh           # install
#   bash scripts/install-hooks.sh --uninstall   # remove
#
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
SOURCE="$REPO_ROOT/.githooks/pre-commit"
TARGET="$HOOKS_DIR/pre-commit"

if [[ "${1:-}" == "--uninstall" ]]; then
    if [[ -f "$TARGET" ]] && grep -q "pocket-confidant bump_version" "$TARGET" 2>/dev/null; then
        rm -f "$TARGET"
        echo "removed $TARGET"
    else
        echo "no pocket-confidant hook installed at $TARGET"
    fi
    exit 0
fi

if [[ ! -f "$SOURCE" ]]; then
    echo "error: $SOURCE not found" >&2
    exit 1
fi

cp "$SOURCE" "$TARGET"
chmod +x "$TARGET"
echo "installed $TARGET"
echo "  -> pre-commit now auto-bumps VERSION + metadata.json (when state changes)"
echo "  -> uninstall with: bash scripts/install-hooks.sh --uninstall"
