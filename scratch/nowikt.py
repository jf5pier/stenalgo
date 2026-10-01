import csv,sys,collections,re
sys.path.insert(0,'.')
from util.reportVowelHarmony import alignedUnits
rows=[r for r in csv.DictReader(open('scratch/vowel-harmony-mixed-candidates.tsv'),delimiter='\t') if r['verdict']=='no-wikt']
lem=collections.defaultdict(dict)
for r in csv.DictReader(open('resources/LexiqueMixte.tsv'),delimiter='\t'):
    lem[r['lemme']].setdefault(r['ortho'],r)
print("| # | lemma | context | minority | majority | fr.wiki | preferred |\n|--|--|--|--|--|--|--|")
for i,r in enumerate(rows,1):
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
    pref=jv if int(m)>int(n) else ('?')
    if r['pair']=='E/e' and dbl: pref='E rule'
    if re.search(r'\[o\]t?$',ctx): pref='HOLD -o(t)'
    w=('/'+r['wikt_ipa']+'/ (count differs)') if r['wikt_ipa'] else 'none'
    print(f"| {i} | {r['lemme']} | {ctx} | {mv}×{n} {' '.join(forms.split()[:3])} | {jv}×{m} {r['majority'].split()[0]} | {w} | **{pref}** |")
