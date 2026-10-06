#!/usr/bin/env python3
"""Merge harvest summaries + hand overlay into the shippable catalog (json + tsv)."""
import json, sys, csv
from pathlib import Path
root = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1])
rows = json.load(open(root/'build'/'summaries.json'))
ov = json.load(open(root/'build'/'overlay.json'))
keep = ['source','derived','id','name','url','category','platform','type','group','progress','license','stars','pushed','language','archived','tools','compilers','build','summary']
res = []
for r in rows:
    e = {k: r.get(k) for k in keep}
    o = ov.get(r['id'], {})
    e['use'] = o.get('use', []); e['note'] = o.get('note', ''); e['depth'] = o.get('depth', 'meta' if not r.get('readme_bytes') else 'readme'); e['ai'] = o.get('ai') or ('mentions' if r.get('ai_guess') in ('human-only?', 'mentions') else 'unspecified')
    e['ai_evidence'] = (r.get('ai_evidence') or '')[:160] if e['ai'] == 'mentions' else ''
    if not e['summary']:
        e['summary'] = f"{e['name']} ({e['type']}; {e['platform']})"
    res.append(e)
out.mkdir(parents=True, exist_ok=True)
json.dump(res, open(out/'catalog.json','w'), indent=0, ensure_ascii=False)
with open(out/'catalog.tsv','w',newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['id','category','platform','progress','license','stars','compilers','tools','use','ai','depth','summary'])
    for e in res:
        w.writerow([e['id'], e['category'], e['platform'], e['progress'] if e['progress'] is not None else '', e['license'] or '', e['stars'] or '', ';'.join(e['compilers']), ';'.join(e['tools']), ';'.join(e['use']), e['ai'], e['depth'], (e['note'] or e['summary'])[:300].replace('\t',' ')])
print(len(res), 'entries written to', out)
