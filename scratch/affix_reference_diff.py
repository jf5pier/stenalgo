"""Compare OQLF affix table + TAO/Pluvier seeds against the affix candidate pool and L/M/H selected rules."""
import csv, re, sys, unicodedata
def norm(s): return unicodedata.normalize('NFC', s)
cand=list(csv.DictReader(open('scratch/affix-candidates.tsv'),delimiter='\t'))
anch=[c for c in cand if c['isAnchor']=='1']
sel={}
for s in 'LMH':
    for r in csv.DictReader(open(f'scratch/affix-sweep/{s}/affix-rules.tsv'),delimiter='\t'):
        sel.setdefault(s,[]).append(r)
def orthos(c): return set(norm(c['ortho']).split('|'))
def formsOf(r):
    return r['forms']
def rank_of(c,pos):
    xs=sorted((float(a['freq']) for a in anch if a['position']==pos),reverse=True)
    f=float(c['freq']); return sum(1 for x in xs if x>f)+1
def formHit(f,pos,sp):
    f=re.sub(r'\(k=\d+\)$','',f.split('⟨')[0].strip())
    lits=re.sub(r'\[[^\]]*\]','',f)
    lits=re.sub(r'-\{[^}]*\}','',lits).replace('·','')
    return lits.endswith(sp) if pos=='suffix' else lits.startswith(sp)
def analyse(pos,sp):
    sp=norm(sp); out={}
    hits=[c for c in cand if c['position']==pos and sp in orthos(c)]
    a=[c for c in hits if c['isAnchor']=='1']
    best=max(a,key=lambda c:float(c['freq'])) if a else None
    # selected as root or k=1 form
    insel=''
    for s in 'LMH':
        for r in sel[s]:
            if r['position']==pos and (sp in r['root'].split('|') or re.search(r'(^|\| )'+re.escape(sp)+r'(\||\(k=1\))',r['forms'].split('(k=')[0]) ):
                insel+=s+f"#{r['rank']} "
    # otherwise appears in grown-form of some rule?
    grown=''
    if not insel:
        for s in 'LMH':
            for r in sel[s]:
                if r['position']==pos and any(formHit(f,pos,sp) for f in r['forms'].split(' | ')):
                    grown+=s+f"#{r['rank']}~ "
    return best,insel.strip(),grown.strip(),len(hits)
def reason(best,insel,grown,nh,node=None):
    if insel: return 'SELECTED'
    if grown: return 'inside a grown form of another rule'
    if best is None:
        if node: return f'no k=1 anchor; best grown node freq {float(node["freq"]):.0f}, {node["carriers"]} carriers (not a root by design)'
        return 'no anchor (below pool thresholds / not a single-syllable anchor)' if nh==0 else 'only as grown node, never an anchor'
    exc=int(best['exceptionCount']); car=int(best['carriers']); rate=exc/(exc+car) if exc+car else 0
    bits=[]
    if rate>0.05: bits.append(f'exception rate {rate:.0%}>5% cap')
    if float(best['attestedShare'])<0.5: bits.append(f"pseudo-affix attested {float(best['attestedShare']):.2f}")
    if best['mergeParts']=='' and float(best['newConflictFreq'])>0: bits.append('conflicts')
    return 'candidate unselected: '+'; '.join(bits) if bits else 'candidate unselected: value too low vs. the top 30'
def nodeOf(pos,sp):
    h=[c for c in cand if c['position']==pos and c['isAnchor']!='1' and any(o==sp or (pos=='suffix' and o.endswith(sp)) or (pos=='prefix' and o.startswith(sp)) for o in orthos(c))]
    return max(h,key=lambda c:float(c['freq'])) if h else None
def run(rows,label):
    print(f'\n## {label}\n\n| affix | pos | anchor freq (rank) | carriers | exc rate | attested | selected | verdict |\n|---|---|---|---|---|---|---|---|')
    for pos,sp,extra in rows:
        best,insel,grown,nh=analyse(pos,sp)
        if best:
            exc=int(best['exceptionCount']);car=int(best['carriers'])
            m=(f"{float(best['freq']):.0f} (#{rank_of(best,pos)})",car,f"{exc/(exc+car) if exc+car else 0:.1%}",best['attestedShare'])
        else: m=('-','-','-','-')
        print(f"| {sp}{' '+extra if extra else ''} | {pos} | {m[0]} | {m[1]} | {m[2]} | {m[3]} | {insel or grown or '-'} | {reason(best,insel,grown,nh,nodeOf(pos,sp))} |")
rows=[]
for r in csv.DictReader(open('resources/reference/oqlf_affixes.tsv'),delimiter='\t'):
    for a in re.split(r',\s*',r['affix']):
        a=a.strip().strip('-')
        if a and not a.startswith('vidéo'): rows.append((r['position'],a,''))
    if r['affix'].startswith('vidéo'): rows.append((r['position'],'vidéo',''))
# prune female variants dup like -ante (keep given)
run(rows,'OQLF')
seen=set();rows=[]
for r in csv.DictReader(open('resources/affixSeeds.tsv'),delimiter='\t'):
    k=(r['position'],r['affix'])
    if k in seen: continue
    seen.add(k); rows.append((r['position'],r['affix'],r['pluvier_chord']))
run(rows,'TAO / Pluvier seeds')
