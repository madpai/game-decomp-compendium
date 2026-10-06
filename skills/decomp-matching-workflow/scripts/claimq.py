#!/usr/bin/env python3
"""Tiny atomic claim queue + ledger for parallel workers (agents or humans) on any bulk RE job.

Why: when several agents work the same list (functions to match, symbols to name, files to convert) you need
(1) nobody gets the same item twice, (2) crashed workers' claims expire, (3) every outcome is recorded with a reason,
(4) a lead can sweep and count. State lives in one directory (default ./.claimq); no database, no dependencies.

  claimq.py init items.txt                         one item id per line (optionally "id<TAB>priority", lower first)
  claimq.py claim --id w01 --count 2 [--ttl 7200]  prints claimed ids as JSON; empty list when the queue is drained
  claimq.py renew --id w01 ITEM                    extend a claim while working
  claimq.py done  --id w01 ITEM [--note "..."]     record success
  claimq.py defer --id w01 ITEM --reason "tiebreak: regs swapped" [--needs "..."]   normal outcome, never a failure
  claimq.py release --id w01 ITEM                  give an item back
  claimq.py requeue ITEM...                        move deferred/done items back (lead only)
  claimq.py status                                 counts + deferrals grouped by slug (text before the first colon)
  claimq.py sweep                                  drop expired claims, print per-worker stats

Atomicity: a claim is a file created with os.link from a temp file (fails if the item is already claimed); expiry is
stored in the file and checked on claim. Items are served in priority order (file order if no priority).
"""
import argparse, collections, json, os, sys, time, hashlib

def d(root, *p): return os.path.join(root, *p)
def key(item): return hashlib.sha1(item.encode()).hexdigest()[:16] + '_' + ''.join(c if c.isalnum() or c in '-_.' else '_' for c in item)[:60]
def now(): return time.time()
def load_items(root):
    return [l.rstrip('\n').split('\t') for l in open(d(root, 'items.tsv'), encoding='utf-8') if l.strip()]
def ledger(root, rec):
    rec['t'] = now()
    with open(d(root, 'ledger.jsonl'), 'a', encoding='utf-8') as f: f.write(json.dumps(rec) + '\n')
def state(root):
    """item -> latest status from the ledger ('done'|'deferred'|'released')."""
    s = {}
    p = d(root, 'ledger.jsonl')
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            r = json.loads(line)
            if r['event'] in ('done', 'deferred'): s[r['item']] = r
            elif r['event'] in ('requeue',): s.pop(r['item'], None)
    return s

def cmd_init(a):
    os.makedirs(d(a.root, 'claims'), exist_ok=True)
    rows = [l.rstrip('\n').split('\t') for l in open(a.items, encoding='utf-8') if l.strip()]
    rows = [r if len(r) > 1 else [r[0], '0'] for r in rows]
    rows.sort(key=lambda r: float(r[1]))   # stable: file order within equal priority
    with open(d(a.root, 'items.tsv'), 'w', encoding='utf-8') as f:
        for r in rows: f.write('\t'.join(r[:2]) + '\n')
    print(f'{len(rows)} items')

def claim_path(root, item): return d(root, 'claims', key(item))
def read_claim(p):
    try: return json.load(open(p))
    except (OSError, ValueError): return None

def cmd_claim(a):
    got = []
    st = state(a.root)
    for item, _ in load_items(a.root):
        if len(got) >= a.count: break
        if item in st: continue
        p = claim_path(a.root, item)
        c = read_claim(p)
        if c and c['expires'] > now() and c['worker'] != a.id: continue
        tmp = d(a.root, 'claims', f'.tmp-{a.id}-{os.getpid()}')
        json.dump({'item': item, 'worker': a.id, 'expires': now() + a.ttl}, open(tmp, 'w'))
        try:
            if c: os.unlink(p)               # expired (or ours): replace
            os.link(tmp, p); got.append(item); ledger(a.root, {'event': 'claim', 'item': item, 'worker': a.id})
        except FileExistsError:
            pass                              # lost the race
        finally:
            try: os.unlink(tmp)
            except OSError: pass
    print(json.dumps({'worker': a.id, 'items': got, 'empty': not got}))

def owned(a):
    c = read_claim(claim_path(a.root, a.item))
    if not c or c['worker'] != a.id: sys.exit(f'{a.item} is not claimed by {a.id}')
    return c

def cmd_renew(a):
    c = owned(a); c['expires'] = now() + a.ttl; json.dump(c, open(claim_path(a.root, a.item), 'w')); print('renewed')
def cmd_done(a):
    owned(a); ledger(a.root, {'event': 'done', 'item': a.item, 'worker': a.id, 'note': a.note}); os.unlink(claim_path(a.root, a.item)); print('recorded')
def cmd_defer(a):
    owned(a); ledger(a.root, {'event': 'deferred', 'item': a.item, 'worker': a.id, 'reason': a.reason, 'needs': a.needs}); os.unlink(claim_path(a.root, a.item)); print('deferred')
def cmd_release(a):
    owned(a); ledger(a.root, {'event': 'released', 'item': a.item, 'worker': a.id}); os.unlink(claim_path(a.root, a.item)); print('released')
def cmd_requeue(a):
    for item in a.items: ledger(a.root, {'event': 'requeue', 'item': item})
    print(f'{len(a.items)} requeued')

def cmd_status(a):
    items = [i for i, _ in load_items(a.root)]; st = state(a.root)
    claimed = sum(1 for i in items if (c := read_claim(claim_path(a.root, i))) and c['expires'] > now())
    done = sum(1 for r in st.values() if r['event'] == 'done'); deferred = [r for r in st.values() if r['event'] == 'deferred']
    print(f'total {len(items)}  done {done}  deferred {len(deferred)}  claimed {claimed}  open {len(items) - done - len(deferred) - claimed}')
    slugs = collections.Counter(r['reason'].split(':')[0].strip() for r in deferred)
    for s, n in slugs.most_common(): print(f'  deferred[{s}] {n}')

def cmd_sweep(a):
    expired = 0
    for f in os.listdir(d(a.root, 'claims')):
        if f.startswith('.'): continue
        c = read_claim(d(a.root, 'claims', f))
        if c and c['expires'] <= now():
            os.unlink(d(a.root, 'claims', f)); expired += 1; ledger(a.root, {'event': 'expired', 'item': c['item'], 'worker': c['worker']})
    per = collections.defaultdict(collections.Counter)
    for line in open(d(a.root, 'ledger.jsonl'), encoding='utf-8'):
        r = json.loads(line)
        if 'worker' in r: per[r['worker']][r['event']] += 1
    print(f'expired claims removed: {expired}')
    for w, c in sorted(per.items()): print(f'  {w}: ' + ', '.join(f'{k}={v}' for k, v in sorted(c.items())))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default='.claimq')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('init'); p.add_argument('items'); p.set_defaults(fn=cmd_init)
    p = sub.add_parser('claim'); p.add_argument('--id', required=True); p.add_argument('--count', type=int, default=1); p.add_argument('--ttl', type=int, default=7200); p.set_defaults(fn=cmd_claim)
    for name, fn in (('renew', cmd_renew), ('done', cmd_done), ('defer', cmd_defer), ('release', cmd_release)):
        p = sub.add_parser(name); p.add_argument('--id', required=True); p.add_argument('item'); p.set_defaults(fn=fn)
        if name == 'renew': p.add_argument('--ttl', type=int, default=7200)
        if name == 'done': p.add_argument('--note', default='')
        if name == 'defer': p.add_argument('--reason', required=True); p.add_argument('--needs', default='')
    p = sub.add_parser('requeue'); p.add_argument('items', nargs='+'); p.set_defaults(fn=cmd_requeue)
    sub.add_parser('status').set_defaults(fn=cmd_status); sub.add_parser('sweep').set_defaults(fn=cmd_sweep)
    a = ap.parse_args(); a.fn(a)

if __name__ == '__main__': main()
