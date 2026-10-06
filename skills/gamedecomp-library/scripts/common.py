"""Shared helpers: locate the data folder (local copy first, then a download cache from the public repo)."""
import json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_DATA = os.path.normpath(os.path.join(HERE, '..', 'data'))
REPO = os.environ.get('COMPENDIUM_REPO', 'madpai/game-decomp-compendium')
RAW_BASE = f'https://raw.githubusercontent.com/{REPO}/main/skills/gamedecomp-library/data/'
CACHE = os.path.expanduser('~/.cache/gamedecomp-compendium')
SKILLS_ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))      # sibling skills live next to this one
CLONES = os.environ.get('GAMEDECOMP_CLONES', os.path.expanduser('~/.claude/knowledge-cache/gamedecomp/clones'))

def data_path(name, allow_download=True):
    """Return a path to data/<name>: the skill's own copy, else a cached download from the public repo."""
    p = os.path.join(LOCAL_DATA, name)
    if os.path.isfile(p): return p
    c = os.path.join(CACHE, name)
    if os.path.isfile(c): return c
    if not allow_download: return None
    os.makedirs(CACHE, exist_ok=True)
    try:
        with urllib.request.urlopen(RAW_BASE + name, timeout=60) as r, open(c, 'wb') as f: f.write(r.read())
        return c
    except Exception as e:
        raise SystemExit(f"data file {name} not found locally and download from {RAW_BASE} failed: {e}")

def load(name, default=None):
    try:
        with open(data_path(name), encoding='utf-8') as f: return json.load(f)
    except (SystemExit, FileNotFoundError):
        if default is not None: return default
        raise
