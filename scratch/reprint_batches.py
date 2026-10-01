import sys

# reform1990 old->new pairs (non-exception)
reform = {}
for line in open('resources/reform1990.tsv'):
    if line.startswith('#') or line.startswith('oldSpelling'):
        continue
    f = line.rstrip('\n').split('\t')
    if len(f) < 7 or f[6] == 'True':
        continue
    reform[f[0]] = f[1]
new2old = {v: k for k, v in reform.items()}

def is_reform(w):
    return w in new2old

def is_old(w):
    return w in reform

rows = []
for line in open('scratch/review-batches.txt'):
    canon, droplem, droporth, nc, nd, src, note = line.rstrip('\n').split('\t')
    rows.append((canon, droplem, droporth, nc, nd, src, note))

unmatched = []
out = []
for canon, droplem, droporth, nc, nd, src, note in rows:
    drop = droporth or droplem
    swapped = False
    # reform variant goes left
    if is_reform(drop) and not is_reform(canon):
        canon, drop = drop, canon
        nc, nd = nd, nc
        swapped = True
    elif is_old(canon) and is_reform(drop):
        canon, drop = drop, canon
        nc, nd = nd, nc
        swapped = True
    if src == 'reform1990' and not (is_reform(canon) or is_old(canon)):
        unmatched.append(canon)
    tag = ('VETO' if note.startswith('suggest VETO') else
           'act' if note.startswith('suggest ACTIVE') else
           'UNDEC?' if note.startswith('UNDECIDED') else
           'seed' if src == 'seed' else 'reform')
    clean = note
    for p in ('suggest ACTIVE -- ', 'suggest VETO -- ', 'UNDECIDED -- '):
        clean = clean.removeprefix(p)
    if clean == 'close call or sparse data -- human settles canonical':
        clean = 'close call'
    mark = '*' if swapped else ' '
    out.append((mark, canon, nc, drop, nd, tag, clean))

start, end = int(sys.argv[1]), int(sys.argv[2])
for i, (mark, canon, nc, drop, nd, tag, clean) in enumerate(out[start-1:end], start):
    print(f"{i:3d}.{mark}{canon:<16}({nc:>9})  |  {drop:<16}({nd:>9})  [{tag}] {clean}")
if unmatched:
    print('UNMATCHED-TO-PAIR:', unmatched, file=sys.stderr)
