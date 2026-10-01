import csv,sys,collections,re
sys.path.insert(0,'.')
from util.reportVowelHarmony import alignedUnits
rows=[r for r in csv.DictReader(open('scratch/vowel-harmony-mixed-candidates.tsv'),delimiter='\t') if r['verdict'] in('fix-minority','fix-majority','verb-fix-minority')]
lem=collections.defaultdict(dict)
for r in csv.DictReader(open('resources/LexiqueMixte.tsv'),delimiter='\t'):
    lem[r['lemme']].setdefault(r['ortho'],r)
EXC={'boeuf','oeuf'}
o={'fix-minority':0,'fix-majority':1,'verb-fix-minority':2}
rows.sort(key=lambda r:(o[r['verdict']],r['pair'],r['lemme']))
out=[]
for r in rows:
    if r['lemme'] in EXC: continue
    lax,tense=r['pair'].split('/')
    side,forms=r['minority'].split(': ',1)
    mv=lax if side=='lax' else tense; jv=tense if side=='lax' else lax
    n=r['lax_rows'] if side=='lax' else r['tense_rows']; m=r['tense_rows'] if side=='lax' else r['lax_rows']
    ctx='';dbl=False
    row=lem[r['lemme']].get(r['lemme'])
    if row:
        u=alignedUnits(row);p=int(r['position'])
        if u and p<len(u):
            ctx=''.join(('['+x[3]+']' if x[0]==p else x[3]) for x in u)
            nxt=u[p+1][3] if p+1<len(u) else ''
            dbl=(len(nxt)>=2 and nxt[0]==nxt[1] and nxt[0] not in 'aeiouy') or nxt=='sc'
    pref=r['wikt_vowel']; note=''
    if r['pair']=='E/e' and dbl:
        if pref!='E': note='rule E (wiki: %s)'%pref
        pref='E'; 
        if not note: note='rule E'
    if re.search(r'\[o\]t?$',ctx): pref='HOLD'; note='masc -o(t) / fem -Ot(te): not harmonized'
    out.append(dict(n=0,lemme=r['lemme'],ctx=ctx,minority=f"{mv}×{n} {' '.join(forms.split()[:3])}",majority=f"{jv}×{m} {r['majority'].split()[0]}",wiki=r['wikt_ipa'],preferred=pref,note=note))
for i,x in enumerate(out,1): x['n']=i
w=csv.DictWriter(open('scratch/harmony-queue.tsv','w'),fieldnames=list(out[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(out)
print(len(out),file=sys.stderr)
a=int(sys.argv[1]);b=int(sys.argv[2])
print("| # | lemma | context | minority | majority | fr.wiki | preferred |\n|--|--|--|--|--|--|--|")
for x in out[a-1:b]: print(f"| {x['n']} | {x['lemme']} | {x['ctx']} | {x['minority']} | {x['majority']} | /{x['wiki']}/ | **{x['preferred']}** {x['note']} |")
