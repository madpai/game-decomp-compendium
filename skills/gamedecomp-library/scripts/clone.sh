#!/usr/bin/env bash
# Shallow-clone catalog projects for reading. usage: clone.sh ID_OR_OWNER/REPO [...]   |   clone.sh --deep
#   ids are catalog ids (query.py shows them), e.g. clone.sh veradictus--thief3-decomp
#   --deep clones every entry the snapshot marks depth=deep (about 30 repos, several hundred MB)
# Clones go to $GAMEDECOMP_CLONES (default ~/.claude/knowledge-cache/gamedecomp/clones). Projects whose README forbids
# agent use (ai=human-only) are refused: reading is not the issue, the project asked agents to stay out.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dest="${GAMEDECOMP_CLONES:-$HOME/.claude/knowledge-cache/gamedecomp/clones}"
mkdir -p "$dest"
resolve() { python3 - "$here/../data/catalog.json" "$1" <<'PY'
import json,sys
cat=json.load(open(sys.argv[1])); q=sys.argv[2]
for e in cat:
    if e['id']==q or e['url'].rstrip('/').endswith('/'+q) or q==e['url']:
        if e['ai']=='human-only': print('REFUSED human-only'); sys.exit(0)
        print(e['url']); sys.exit(0)
print('UNKNOWN')
PY
}
list=("$@")
if [ "${1:-}" = "--deep" ]; then
  mapfile -t list < <(python3 -c "
import json;[print(e['id']) for e in json.load(open('$here/../data/catalog.json')) if e['depth']=='deep' and e['ai']!='human-only']")
fi
for q in "${list[@]}"; do
  url=$(resolve "$q")
  case "$url" in
    REFUSED*) echo "skip $q: project asks agents/AI to stay out"; continue;;
    UNKNOWN) url="https://github.com/$q";;
  esac
  name=$(basename "${url%.git}")
  if [ -d "$dest/$name" ]; then echo "have $name"; continue; fi
  git clone -q --depth 1 "$url.git" "$dest/$name" 2>/dev/null && echo "ok $name" || echo "FAIL $q"
done
