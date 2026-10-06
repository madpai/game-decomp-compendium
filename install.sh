#!/usr/bin/env bash
# Install the skills into an agent skills folder (default: ~/.claude/skills). Re-run to update.
#   ./install.sh                 copy
#   ./install.sh --link          symlink instead (edits in this clone take effect immediately)
#   SKILLS_DIR=/path ./install.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dest="${SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$dest"
for s in "$here"/skills/*/; do
  name="$(basename "$s")"
  if [ "${1:-}" = "--link" ]; then rm -rf "${dest:?}/$name"; ln -s "$s" "$dest/$name"
  else rm -rf "${dest:?}/$name"; cp -r "$s" "$dest/$name"; fi
  find "$dest/$name" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
  echo "installed $name -> $dest/$name"
done
python3 "$dest/gamedecomp-library/scripts/selftest.py" --skills-root "$dest" || echo "(selftest reported issues; see above)"
