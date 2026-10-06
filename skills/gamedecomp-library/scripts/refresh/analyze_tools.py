#!/usr/bin/env python3
import json, re, glob, collections
from pathlib import Path
root = Path(__file__).resolve().parent
cat = json.load(open(root / 'catalog.json'))
extra_path = root / 'extra_catalog.json'
for _p in cat['projects']: _p.setdefault('source', 'GameDecompLibrary')
if extra_path.exists():
    cat['projects'] = cat['projects'] + json.load(open(extra_path))['projects']
TOOLS = {
 'objdiff':r'\bobjdiff\b','asm-differ':r'asm[-_ ]differ|diff\.py','decomp-permuter':r'permuter','m2c':r'\bm2c\b|mips_to_c','dtk':r'\bdtk\b|decomp-toolkit',
 'splat':r'\bsplat\b','spimdisasm':r'spimdisasm','ghidra':r'ghidra','ida':r'\bIDA( Pro| Free)?\b|\.idb|IDAPython','binary-ninja':r'binary ?ninja','radare2':r'radare|rizin|cutter',
 'reccmp':r'reccmp|isledecomp','ninja':r'\bninja\b','wibo':r'\bwibo\b','wine':r'\bwine\b','docker':r'docker','cmake':r'cmake','mwcc':r'\bmwcc\b|metrowerks|codewarrior',
 'ido':r'\bIDO\b','gcc':r'\bgcc\b','msvc':r'\bMSVC\b|Visual C\+\+|cl\.exe|Visual Studio','clang':r'\bclang\b','psyq':r'psy-?q','maspsx':r'maspsx','devkitpro':r'devkit(PPC|ARM|Pro)',
 'decomp.dev':r'decomp\.dev','progress-report':r'report\.json|progress\.json|progress badge|\bbadge','n64sym':r'n64sym|ido-static-recomp','ppcdis':r'ppcdis','rust':r'\brust\b|cargo',
 'xenia':r'xenia','xenonrecomp':r'xenonrecomp|XenonRecomp','dolphin':r'\bdolphin\b','mame':r'\bMAME\b','dosbox':r'dosbox','frida':r'\bfrida\b','capstone':r'capstone','unicorn':r'unicorn',
 'discord':r'discord\.gg','assets-extract':r'extract(ed)? (assets|from your own)|ROM|disc image|iso\b','sha1':r'sha-?1|sha256|hash','python':r'python',
}
BUILD = {'configure.py':'ninja configure.py','Makefile':'make','makefile':'make','CMakeLists.txt':'cmake','build.ninja':'ninja','objdiff.json':'objdiff.json','Cargo.toml':'cargo','splat.yaml':'splat','decomp.yaml':'decomp.yaml',
 'meson.build':'meson','Dockerfile':'docker','docker-compose.yml':'docker','tools':'tools/','asm':'asm/','config':'config/','symbols.txt':'symbols.txt','splits.txt':'splits.txt','reccmp-project.yml':'reccmp','pyproject.toml':'python','requirements.txt':'python','.github':'ci','src':'src/','include':'include/','docs':'docs/'}
out=[]; tech=collections.defaultdict(collections.Counter); langs=collections.Counter()
for p in cat['projects']:
    f = root/'raw'/(p['id']+'.json')
    if not f.exists(): continue
    r = json.load(open(f)); rd = r.get('readme','') or ''
    names = {n for n,_ in r.get('root',[])}
    row = {'id':p['id'],'name':p['name'],'url':p['url'],'category':p['category'],'platform':p.get('platform'),'type':p.get('type'),'group':p.get('group'),'description':p.get('description',''),'source':p.get('source'),
           'progress':(p.get('progress') or {}).get('decompiled'),'linked':(p.get('progress') or {}).get('linked'),'methods':[m['id'] for m in p.get('method_tags',[])]}
    m=r.get('meta') or {}
    row.update(stars=m.get('stargazers_count'),license=m.get('license'),pushed=m.get('pushed_at','')[:10] if m.get('pushed_at') else None,archived=m.get('archived'),language=m.get('language'),topics=m.get('topics'),size_kb=m.get('size'),branch=m.get('default_branch'))
    row['tools']=sorted(k for k,rx in TOOLS.items() if re.search(rx,rd,re.I))
    row['build']=sorted({BUILD[n] for n in names if n in BUILD})
    row['root']=sorted(names)[:40]
    row['readme_bytes']=len(rd)
    out.append(row)
    for t in row['tools']: tech[(p.get('platform') or '?').split()[0] if p['category']=='decomp' else 'tool'][t]+=1
json.dump(out,open(root/'index.json','w'),indent=0)
print(len(out))
for plat,c in sorted(tech.items(), key=lambda kv:-sum(kv[1].values()))[:14]:
    print(plat, c.most_common(12))
lic=collections.Counter(r['license'] for r in out); print(lic.most_common(12))
