#!/usr/bin/env bash
# Maintainer helper: sync skills edited in ~/.claude/skills into this repo, validate, and show what changed.
# It never pushes; review `git status` / `git diff --stat`, then commit and push yourself.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
src="${SKILLS_DIR:-$HOME/.claude/skills}"
for s in "$here"/skills/*/; do
  name="$(basename "$s")"
  [ -d "$src/$name" ] && rsync -a --delete --exclude __pycache__ --exclude '*.pyc' "$src/$name/" "$here/skills/$name/"
done
python3 "$here/skills/gamedecomp-library/scripts/selftest.py" --skills-root "$here/skills"
git -C "$here" status --short | head -30
