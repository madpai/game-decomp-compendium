#!/usr/bin/env python3
"""Harvest metadata, README and root listing for every catalog project (public GitHub data only)."""
import json, subprocess, sys, re, concurrent.futures as cf
from pathlib import Path
root = Path(__file__).resolve().parent
raw = root / 'raw'
import os
catalog = json.load(open(sys.argv[1] if len(sys.argv) > 1 else root / "catalog.json"))

def gh(path, accept=None, timeout=60):
    cmd = ['gh', 'api', path]
    if accept: cmd += ['-H', 'Accept: ' + accept]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout, r.stderr

def one(p):
    out = raw / (p['id'] + '.json')
    if out.exists():
        return p['id'], 'cached'
    m = re.match(r'https://github\.com/([^/]+)/([^/#?]+)', p['url'])
    rec = {'id': p['id'], 'url': p['url']}
    if not m:
        rec['host'] = 'non-github'
        out.write_text(json.dumps(rec)); return p['id'], 'non-github'
    owner, repo = m.group(1), m.group(2).removesuffix('.git')
    rc, so, se = gh(f'repos/{owner}/{repo}')
    if rc != 0:
        rec['error'] = se[:200]; out.write_text(json.dumps(rec)); return p['id'], 'error'
    meta = json.loads(so)
    rec['meta'] = {k: meta.get(k) for k in ('full_name', 'description', 'language', 'stargazers_count', 'forks_count', 'pushed_at', 'archived', 'topics', 'default_branch', 'size', 'homepage', 'fork', 'open_issues_count', 'created_at')}
    rec['meta']['license'] = (meta.get('license') or {}).get('spdx_id')
    rc, so, _ = gh(f'repos/{owner}/{repo}/languages')
    if rc == 0: rec['languages'] = json.loads(so)
    branch = meta.get('default_branch') or 'main'
    rc, so, _ = gh(f'repos/{owner}/{repo}/git/trees/{branch}')
    if rc == 0:
        rec['root'] = [(t['path'], t['type'][0]) for t in json.loads(so).get('tree', [])]
    rc, so, _ = gh(f'repos/{owner}/{repo}/readme', 'application/vnd.github.raw')
    if rc == 0: rec['readme'] = so[:60000]
    out.write_text(json.dumps(rec))
    return p['id'], 'ok'

with cf.ThreadPoolExecutor(8) as ex:
    for n, (pid, st) in enumerate(ex.map(one, catalog['projects']), 1):
        if st != 'cached' and (n % 25 == 0 or st != 'ok'):
            print(n, pid, st, flush=True)
print('done', len(list(raw.glob('*.json'))))
